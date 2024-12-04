# 本探し

HonSagashi - A Calibre metadata source plugin for Japanese book.

一个专用于获取日文图书元数据的calibre插件。

## 功能特性

本插件可以根据“ISBN”、“NDL书目ID”、“书名+作者”三类条件自动从日本国立国会图书馆检索以下图书元数据：

* 书名、作者、出版社、出版时间
* 标签（图书类别信息）：**支持[日本十进分类法（NDC）](https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E5%8D%81%E9%80%B2%E5%88%86%E9%A1%9E%E6%B3%95)和[国立国会图书馆分类表（NDLC）](https://ja.wikipedia.org/wiki/%E5%9B%BD%E7%AB%8B%E5%9B%BD%E4%BC%9A%E5%9B%B3%E6%9B%B8%E9%A4%A8%E5%88%86%E9%A1%9E%E8%A1%A8)。**
* ISBN、国立国会图书馆书目ID（NDLBibID）、日本全国书目编号（JPNO）：**即使是1981年之前无ISBN的日语图书同样可以得到较好的支持！**

## 测试&开发

请使用`calibre-customize -b .`将该插件添加入calibre测试效果。

或者使用`calibre-debug -e __init__.py`运行测试用例进行测试。

编写完成后，请使用`black __init__.py`格式化代码。

如果修改了插件选项、获取封面的功能，请在调试时重启calibre以看到最新效果。

如果对插件的工作原理有任何疑问，可以参考[Calibre官方文档中的相应部分](https://manual.calibre-ebook.com/zh_CN/plugins.html#module-calibre.ebooks.metadata.sources.base)，以及[Calibre自带的元数据插件](https://github.com/kovidgoyal/calibre/tree/master/src/calibre/ebooks/metadata/sources)。

## 参考&致谢

* 本项目受[NLCISBNPlugin](https://github.com/DoiiarX/NLCISBNPlugin)激励而产生，并参考了其实现。
* 本项目基于日本国立国会图书馆对外公开的API开发，相关文档如下：
    - [日本国立国会图书馆对外开放接口规格书](https://ndlsearch.ndl.go.jp/file/help/api/specifications/ndlsearch_api_20240712.pdf)
    - [日本国立国会图书馆数据原型与对外接口对应关系一览表](https://ndlsearch.ndl.go.jp/file/help/api/specifications/ndlsearch_api_ap1_20241015.pdf)
