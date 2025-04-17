#!/usr/bin/env python3
import sys
import tempfile
import subprocess

def main():
    fh_in = sys.stdin
    fh_out = sys.stdout

    # 使用する objdump コマンド (環境に合わせて確認・変更)
    objdump_cmd = "riscv32-unknown-elf-objdump"

    while True:
        line = fh_in.readline()
        if not line:
            return 0

        # 前後の空白文字（改行含む）を除去
        hex_instruction = line.strip()

        # 空行はスキップ
        if not hex_instruction:
            fh_out.write(line) # 元の行をそのまま出力
            fh_out.flush()
            continue

        # 元のコードの 'x' を含む行の処理 (そのまま出力)
        if "x" in hex_instruction:
            fh_out.write(line) # 元の行をそのまま出力
            fh_out.flush()
            continue
        else:
            try:
                # 16進文字列を整数に変換
                instruction_int = int(hex_instruction, 16)
                # 整数を32ビットのリトルエンディアンのバイト列に変換
                # RISC-V は通常リトルエンディアン
                instruction_bytes = instruction_int.to_bytes(4, byteorder='little')
            except ValueError:
                print(f"Error: '{hex_instruction}' is not valid hex number", file=sys.stderr)
                continue
            except OverflowError:
                print(f"Error: '{hex_instruction}' is over 32bit", file=sys.stderr)
                continue


            # 一時ファイルにバイナリデータを書き込む (with文で自動削除)
            try:
                with tempfile.NamedTemporaryFile(mode='wb', delete=False) as bin_temp:
                    bin_temp.write(instruction_bytes)
                    temp_filename = bin_temp.name # ファイル名を保持

                # objdump を実行して逆アセンブル
                # -D: 全体を逆アセンブル
                # -b binary: 入力は生バイナリ
                # -m riscv:rv32i: アーキテクチャを明示的に指定 (重要！)
                # -M no-aliases,numeric: エイリアスを表示しない、数値で表示
                result = subprocess.run(
                    [objdump_cmd, "-D", "-b", "binary", "-m", "riscv:rv32i", "-M","no-aliases,numeric", temp_filename],
                    capture_output=True,
                    check=True, # エラーがあれば例外発生
                    encoding='utf-8', # 出力を文字列として扱う
                    errors='ignore'   # デコードエラーは無視
                )
                #print(result.stdout) # デバッグ用にobjdumpの出力を表示

                lastline = result.stdout.splitlines()[-1]
                chunks = lastline.split('\t')
                if len(chunks) < 3:
                    print(f"Error: Unexpected output format from objdump", file=sys.stderr)
                    print(f"Output: {lastline}", file=sys.stderr)
                    fh_out.write(line) # 元の行をそのまま出力
                    fh_out.flush()
                    continue
                else:
                    opcodes = " ".join(chunks[2:])
                    fh_out.write("%s\n" % opcodes)
                    fh_out.flush()
                
            except subprocess.CalledProcessError as e:
                print(f"Error: fail during {objdump_cmd}", file=sys.stderr)
                print(f"command: {' '.join(e.cmd)}", file=sys.stderr)
                print(f"Error output:\n{e.stderr}", file=sys.stderr)
            except FileNotFoundError:
                print(f"Error: command '{objdump_cmd}' not found. check your PATH", file=sys.stderr)
            except Exception as e:
                print(f"Unexpected Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())
