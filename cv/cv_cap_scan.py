# -*- coding: utf-8 -*-

def main():
    # コマンド引数の解釈
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cameraID", nargs='?', type=int, default=0,
                   help="Camera ID (default: %(default)s)")
    p.add_argument("-DS", "--DSHOW", action='store_true',
                   help="With DirectShow (default: %(default)s)")
    p.add_argument("-B", "--build-info", action='store_true',
                   help="Show build information (default: %(default)s)")
    p.add_argument("-T", "--try-msmf-workaround", action='store_true',
                   help="Set OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS=0 "
                   "(default: %(default)s)")
    args = p.parse_args()

    if args.try_msmf_workaround and not args.DSHOW:
        # 使っているカメラによるのかもしれないが、
        # カメラの起動に、異常に時間がかかる場合の回避策。
        # import cv2 より前にすること。
        import os
        os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

    import cv2
    if args.build_info:
        # cv2 構築時の情報を出力
        print(cv2.getBuildInformation())

    # VideoCapture 取得
    if args.DSHOW:
        print(f'Camera #{args.cameraID}, with DSHOW')
        cap = cv2.VideoCapture(args.cameraID, cv2.CAP_DSHOW)
    else:
        print(f'Camera #{args.cameraID}, without DSHOW')
        cap = cv2.VideoCapture(args.cameraID)

    if not cap.isOpened():
        raise RuntimeError(f'Not opened camera #{args.cameraID}')

    # 見付かったプロパティをとりあえず全部出力してみる。
    # 値が -1 ならば、カメラが対応していないプロパティ（だと思う、たぶん）。
    for k in vars(cv2):
        if k.startswith('CAP_PROP_'):
            print(k, cap.get(getattr(cv2, k)))

    cap.release()


if __name__ == '__main__':
    main()
