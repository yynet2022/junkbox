# -*- coding:utf-8 -*-
import tkinter.messagebox as tkMessageBox
import ctypes
import locale

ES_CONTINUOUS = 0x80000000
ES_AWAYMODE_REQUIRED = 0x00000040
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


# 動作しているかは、管理者権限で
# powercfg requests
# で確認できる。
def main():
    locale.setlocale(locale.LC_ALL, '')
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED | ES_CONTINUOUS)
    tkMessageBox.showinfo('スリープ抑制 - 情報', 'スリープ抑制中')


if __name__ == '__main__':
    main()
