import ctypes
import random
import time
import string
import concurrent.futures
from ctypes.wintypes import MSG
from wkeStruct import *

NODE_DLL_FILE_PATH = 'D:/yiguo/pyblink/lib/node.dll'


def method(proto_type):
    """c类型装饰器，用于传参"""
    class MethodDescriptor(object):
        __slots__ = ['func', 'bound_funcs']

        def __init__(self, func):
            self.func = func
            self.bound_funcs = {}  # keep reference, avoid gc

        def __get__(self, obj, obj_type=None):
            if obj is not None:
                # noinspection PyBroadException
                try:
                    return self.bound_funcs[obj, obj_type]
                except Exception:
                    ret = self.bound_funcs[obj, obj_type] = proto_type(
                        self.func.__get__(obj, obj_type))
                    return ret
            return None
    return MethodDescriptor


class BlinkWindow(object):
    def __init__(self, *args, **kwargs):
        self._width = 1024
        self._height = 768
        self.webview = 0
        self.mb = ctypes.cdll.LoadLibrary(NODE_DLL_FILE_PATH)
        self.mb.wkeInitialize()
        super().__init__(*args, **kwargs)

    def __del__(self):
        if self.mb:
            self.mb.wkeFinalize()
        return

    def get(self, target_url):
        webview = self.create_window(self._width, self._height)
        # self.set_headless(webview)
        self.move_to_center(webview)
        self.set_window_title(webview, "MiniBlink Python Crawler V3.2")
        self.wkeOnDocumentReady2(webview)
        self.wkeOnWindowClosing(webview)
        self.wkeOnWindowDestroy(webview)
        self.show_window(webview)
        self.set_webview_proxy(webview, '183.147.214.209', '3265')
        self.load_url(webview, target_url)
        self.message_loop(webview)
        print('cookie: {}'.format(self.get_cookie(webview)))

    def create_window(self, width, height, _type=0,  x=0, y=0, hwnd=0):
        """创建一个webview"""
        # _type 0:普通窗口,1:透明窗口(可用于离屏渲染),2:嵌入式窗口
        # 若要嵌入在父窗口里的子窗口,hwnd需要设置
        webview = self.mb.wkeCreateWebWindow(
            _type, hwnd, x, y,
            width, height
        )
        return webview

    def message_loop(self, webview=None):
        """msg load循环接受消息直到没有，等待页面加载完成"""
        msg = MSG()
        ret = 1
        while ret > 0:
            ret = user32.GetMessageW(byref(msg), None, 0, 0)
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))

    @method(CFUNCTYPE(None, c_int, c_void_p, c_void_p))
    def handle_document_ready2(self, webview, param, frame_id):
        """对应js里的body onload事件, ready2是可以判断是否是主frame

        Return: stop loading: True, continue loading: False
        """
        # 判断需要获取的源代码url
        # tmp_url = 'https://www.httpbin.org/ip'
        tmp_url = 'https://www.amazon.com'
        url = self.get_frame_url(webview, frame_id)
        if url != tmp_url:
            return False

        page_source = self.get_source(webview)
        return False

    def get_source(self, webview, is_save=True):
        source_ptr = self.mb.wkeGetSource(webview)
        page_source = c_char_p(source_ptr).value
        if is_save:
            rand_num = ''.join(random.choice(string.ascii_letters)
                               for _ in range(6))
            file_name = "D:/yiguo/pyblink/tmp/amz_" + rand_num + ".html"
            with open(file_name, "wb+") as tmp_file:
                tmp_file.write(page_source)
        return page_source

    def get_frame_url(self, webview, frame_id):
        url = self.mb.wkeGetFrameUrl(webview, frame_id)
        url = c_char_p(url).value
        return url.decode()

    @method(CFUNCTYPE(None, c_int, c_void_p))
    def handle_window_destroy(self, webview, param):
        ctypes.windll.user32.PostQuitMessage(0)

    @method(CFUNCTYPE(c_bool, c_int, c_void_p))
    def handle_window_closing(self, webview, param):
        return 6  # IDYES=6

    # 下列为页面操作
    def move_to_center(self, webview):
        self.mb.wkeMoveToCenter(webview)

    # 下列为浏览器属性操作
    def set_window_title(self, webview, title):
        self.mb.wkeSetWindowTitleW(webview, title)

    def set_headless(self, webview, _bool=True):
        """设置无头模式,提高性能(目前无头和窗口模式不能同时实现)"""
        self.mb.wkeSetHeadlessEnabled(webview, _bool)

    # 设置指定webview的代理
    def set_webview_proxy(self, webview, ip, port, proxy_type=1, user=None, password=None):
        # proxy_type={
        # 0:WKE_PROXY_NONE,
        # 1:WKE_PROXY_HTTP,
        # 2:WKE_PROXY_SOCKS4,
        # 3:WKE_PROXY_SOCKS4A,
        # 4:WKE_PROXY_SOCKS5,
        # 5:WKE_PROXY_SOCKS5HOSTNAME}
        # ip='49.87.18.53'
        # port=4221
        if user == None:
            user = b''
        else:
            user = user.encode('utf8')
        if password == None:
            password = b''
        else:
            password = password.encode('utf8')
        ip = ip.encode('utf8')
        port = int(port)
        proxy = wkeProxy(type=c_int(proxy_type), hostname=ip,
                         port=c_ushort(port), username=user, password=password)
        self.mb.wkeSetViewProxy(webview, byref(proxy))

    def set_proxy(self, ip, port, proxy_type=4, user=None, password=None):
        # proxy_type={
        # 0:WKE_PROXY_NONE,
        # 1:WKE_PROXY_HTTP,
        # 2:WKE_PROXY_SOCKS4,
        # 3:WKE_PROXY_SOCKS4A,
        # 4:WKE_PROXY_SOCKS5,
        # 5:WKE_PROXY_SOCKS5HOSTNAME}
        if user == None:
            user = b''
        else:
            user = user.encode('utf8')
        if password == None:
            password = b''
        else:
            password = password.encode('utf8')
        ip = ip.encode('utf8')
        port = int(port)
        proxy = wkeProxy(type=c_int(proxy_type), hostname=ip,
                         port=c_ushort(port), username=user, password=password)
        self.mb.wkeSetProxy(byref(proxy))

    # 下列浏览器操作
    def load_url(self, webview, url):
        """加载url"""
        self.mb.wkeLoadURLW(webview, url)

    def reload(self, webview):
        self.mb.wkeReload(webview)

    # 下列cookies相关操作
    def get_cookie(self, webview):
        cookie = c_wchar_p(self.mb.wkeGetCookieW(webview))
        return cookie.value

    def set_cookie(self, webview, url, cookie):
        # cookie格式PERSONALIZE=123;expires=Monday, 13-Jun-2022 03:04:55 GMT
        cookie = cookie.split(';')
        for x in cookie:
            self.mb.wkeSetCookie(webview, url.encode('utf8'), x.encode('utf8'))
        # 设置后要写入cookies.dat文件,才生效
        self.mb.wkePerformCookieCommand(webview, 2)

    def clear_all_cookie(self, webview):
        self.mb.wkeClearCookie(webview)

    # 下列为封装的函数，方便外部调用
    def wkeOnDocumentReady2(self, webview, param=0):
        self.mb.wkeOnDocumentReady2(
            webview, self.handle_document_ready2, param)

    def wkeOnWindowDestroy(self, webview, param=0):
        self.mb.wkeOnWindowDestroy(webview, self.handle_window_destroy, param)

    def wkeOnWindowClosing(self, webview, param=0):
        self.mb.wkeOnWindowClosing(webview, self.handle_window_closing, param)

    def show_window(self, webview, _bool=True):
        self.mb.wkeShowWindow(webview, _bool)


def test_threads():
    window = BlinkWindow()
    # window.set_proxy('127.0.0.1', '9070')
    # test_url = 'https://www.httpbin.org/ip'
    test_url = 'https://www.amazon.com'
    window.get(test_url)
    time.sleep(10)


if __name__ == '__main__':
    # with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
    #     for _ in range(2):
    #         executor.submit(test_threads)
    test_threads()
