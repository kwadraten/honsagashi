# 本探し

HonSagashi - A Calibre metadata source plugin for Japanese book.

一个专用于获取日文图书元数据的calibre插件。

## 测试&开发

请使用`calibre-customize -b .`将该插件添加入calibre测试效果。

或者使用`calibre-debug -e __init__.py`运行测试用例进行测试。

编写完成后，请使用`black __init__.py`格式化代码。

如果对插件的工作原理有任何疑问，可以参考[Calibre官方文档中的相应部分](https://manual.calibre-ebook.com/zh_CN/plugins.html#module-calibre.ebooks.metadata.sources.base)，以及[Calibre自带的元数据插件](https://github.com/kovidgoyal/calibre/tree/master/src/calibre/ebooks/metadata/sources)。

## 参考&致谢

* 本项目受[NLCISBNPlugin](https://github.com/DoiiarX/NLCISBNPlugin)激励而产生，并参考了其实现。
* 本项目基于日本国立国会图书馆对外公开的API开发，相关文档如下：
    - [日本国立国会图书馆对外开放接口规格书](https://ndlsearch.ndl.go.jp/file/help/api/specifications/ndlsearch_api_20240712.pdf)
    - [日本国立国会图书馆数据原型与对外接口对应关系一览表](https://ndlsearch.ndl.go.jp/file/help/api/specifications/ndlsearch_api_ap1_20241015.pdf)
