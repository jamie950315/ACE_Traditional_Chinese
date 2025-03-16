#!/usr/bin/env python3
import io
import time
import enum
import struct
import pathlib
import asyncio
import aiofiles
import numpy as np
import os
from opencc import OpenCC

# 計算 FNV1A-64 雜湊
class FnvHash:
    FNV_64_PRIME = 0x100000001B3
    FNV1_64A_OFF = 0xCBF29CE484222325

    @staticmethod
    def fnv1a_64(data: bytes) -> int:
        assert isinstance(data, bytes)
        h = FnvHash.FNV1_64A_OFF
        for b in data:
            h = ((h ^ b) * FnvHash.FNV_64_PRIME) % (2 ** 64)
        return h

# 單筆檔案結構解析
class KsPckFile:
    FILE_PATH_SZ = 0xE0

    class FileFlags(enum.IntFlag):
        Directory = (1 << 0),
        XorCipher = (1 << 8),

    def __init__(self, raw: bytes):
        self.raw = io.BytesIO(raw)
        max_path = self.FILE_PATH_SZ
        self.file_path = struct.unpack(f"<{max_path}s", self.raw.read(max_path))[0]
        self.align_0E0 = struct.unpack("<i", self.raw.read(4))[0]
        self.inf_flags = struct.unpack("<h", self.raw.read(2))[0]
        self.path_leng = struct.unpack("<h", self.raw.read(2))[0]
        self.path_fnv1 = struct.unpack("<Q", self.raw.read(8))[0]
        self.file_size = struct.unpack("<q", self.raw.read(8))[0]
        self.file_offs = struct.unpack("<q", self.raw.read(8))[0]
        # 依據 path_leng 去除尾端 null 字元
        self.file_path = str(self.file_path[:self.path_leng].decode())
        self.inf_flags = KsPckFile.FileFlags(self.inf_flags)
        return

# KsPkg 解析與解包類別
class KsPck:
    FILE_TBL_SZ = (2 << 24)  # 32 MB
    FILE_ITM_SZ = (1 << 8)   # 256 bytes

    def __init__(self, kspkg_path: str):
        print(f"Parsing input KsPkg file: '{kspkg_path}'")
        self.files = {}
        self.kspkg_path = kspkg_path
        self.fp = open(kspkg_path, "rb")
        self.xork = None
        self.ftbl = None

    def parse_file_tbl(self) -> None:
        # 讀取檔案表
        self.fp.seek(-self.FILE_TBL_SZ, 2)
        self.ftbl = self.fp.read(self.FILE_TBL_SZ)
        # 取得 XOR 金鑰（檔案表最後 8 個位元組）
        self.xork = self.ftbl[-8:]
        ascii_key = ''.join(f"{b:02X}" for b in self.xork)
        print(f"File Table XOR Key: {ascii_key}")
        print("Unciphering KsPkg file table...\n")
        # 利用 numpy 向量化 XOR 運算解密檔案表
        self.ftbl = bytearray(xor_numpy(self.ftbl, self.xork))
        # 依據每筆 256 bytes 結構解析檔案項目
        for i in range(0, int(self.FILE_TBL_SZ / self.FILE_ITM_SZ)):
            idx = i * self.FILE_ITM_SZ
            file_entry = self.ftbl[idx : idx + self.FILE_ITM_SZ]
            file_entry = KsPckFile(file_entry)
            # 若 FNV1A hash 為 0 則結束解析
            if file_entry.path_fnv1 == 0:
                break
            self.files[file_entry.path_fnv1] = file_entry

    def run_unpacked(self) -> None:
        try:
            if self.fp:
                self.fp.close()
            print("\nForcing AC:Evo to use unpacked content...")
            ace_kspkg = pathlib.Path(self.kspkg_path).resolve()
            if ace_kspkg.exists() and ace_kspkg.is_file():
                ace_kspkg.rename(f"{ace_kspkg}.bkup")
        except PermissionError as e:
            print(f"Unable to rename KsPkg, exception: {e}")

# numpy 向量化 XOR 運算
def xor_numpy(data: bytes, xork: bytes) -> bytes:
    arr = np.frombuffer(data, dtype=np.uint8)
    key_arr = np.frombuffer(xork, dtype=np.uint8)
    tiled = np.resize(key_arr, arr.shape)
    result = np.bitwise_xor(arr, tiled)
    return result.tobytes()

# 進度追蹤器
class ProgressTracker:
    def __init__(self, total):
        self.total = total
        self.completed = 0
        self.lock = asyncio.Lock()

    async def update(self):
        async with self.lock:
            self.completed += 1
            self.print_progress()

    def print_progress(self):
        percentage = (self.completed / self.total) * 100 if self.total else 100
        bar_length = 40
        filled_length = int(bar_length * self.completed // self.total) if self.total else bar_length
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        print(f'\rProgress: |{bar}| {percentage:.2f}% ({self.completed}/{self.total})', end='', flush=True)

# 非同步提取單一檔案，加入 semaphore 及進度追蹤器
async def extract_file_async(file_entry: KsPckFile, kspkg_path: str, out_path: str, xork: bytes, sem: asyncio.Semaphore, progress_tracker: ProgressTracker):
    async with sem:
        async with aiofiles.open(kspkg_path, mode="rb") as f:
            await f.seek(file_entry.file_offs)
            data = await f.read(file_entry.file_size)
    # 若有 XOR 加密，使用執行緒池執行 numpy XOR 運算
    if KsPckFile.FileFlags.XorCipher in file_entry.inf_flags:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, xor_numpy, data, xork)
    # 設定輸出檔案路徑
    file_path = pathlib.Path(file_entry.file_path)
    if out_path.casefold() != "content":
        file_path = pathlib.Path(out_path) / file_path
    # 處理目錄與檔案
    if KsPckFile.FileFlags.Directory in file_entry.inf_flags:
        file_path.mkdir(parents=True, exist_ok=True)
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, mode="wb") as f:
            await f.write(data)
    await progress_tracker.update()

# 非同步平行提取所有檔案，並以 semaphore 限制同時開啟檔案數量
async def extract_all_async(pck: KsPck, out_path: str):
    total_files = len(pck.files)
    progress_tracker = ProgressTracker(total_files)
    sem = asyncio.Semaphore(10)  # 同時只允許 10 個任務開啟檔案
    tasks = []
    for file_entry in pck.files.values():
        tasks.append(
            extract_file_async(file_entry, pck.kspkg_path, out_path, pck.xork, sem, progress_tracker)
        )
    await asyncio.gather(*tasks)
    print()  # 換行結束進度條輸出

# 轉換 localization 檔案（簡轉台灣正體）
def convert_localization_files(out_path: str):
    localization_dir = os.path.join(out_path, "uiresources", "localization")
    filenames = ["cn.tooltips.loc", "cn.loc", "cn.cars.loc"]
    cc = OpenCC('s2twp')
    for filename in filenames:
        file_path = os.path.join(localization_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            converted_content = cc.convert(content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
            print(f"{filename} 已成功轉換並覆蓋。")
        else:
            print(f"找不到檔案：{filename}")

# 主流程：解析檔案表、平行提取檔案、轉換 localization 檔案、重命名原始檔案
async def main():
    kspkg_path = r"C:\Program Files (x86)\Steam\steamapps\common\Assetto Corsa EVO\content.kspkg"
    # 將解包目錄設定為遊戲安裝資料夾
    out_path = r"C:\Program Files (x86)\Steam\steamapps\common\Assetto Corsa EVO"
    pck = KsPck(kspkg_path)
    pck.parse_file_tbl()
    start = time.perf_counter()
    await extract_all_async(pck, out_path)
    print(f"\nExtraction completed in {time.perf_counter() - start:.3f} seconds.")
    
    # 開始轉換 localization 檔案
    print("\n開始轉換 localization 檔案...")
    convert_localization_files(out_path)
    
    pck.run_unpacked()

if __name__ == "__main__":
    asyncio.run(main())
