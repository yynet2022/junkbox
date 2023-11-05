# -*- coding: utf-8 -*-

def main():
    # コマンド引数の解釈
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cameraID", nargs='?', type=int, default=0,
                   help="Camera ID (default: %(default)s)")
    args = p.parse_args()

    # VideoCapture 取得
    import cv2
    cap = cv2.VideoCapture(args.cameraID, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f'Not opened camera #{args.cameraID}')

    # 設定ウィンドウの立ち上げ
    cap.set(cv2.CAP_PROP_SETTINGS, 1)

    # カメラからの画像を描画
    delay = 5   # [msec]
    ESC = 0x1b  # Escape key
    while True:
        key = cv2.waitKey(delay) & 0xFF
        if key in (ord('q'), ESC):
            break
        ret, img = cap.read()
        if ret:
            cv2.imshow('video image', img)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
