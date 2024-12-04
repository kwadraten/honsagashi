# !/usr/bin/env python
# author: 平方和寒(kwadraten)
# Licensed under Apache License 2.0

import urllib.parse
from calibre.ebooks.metadata.sources.base import Source, Option
from calibre.ebooks.metadata import MetaInformation
from datetime import datetime
from bs4 import BeautifulSoup, ResultSet
import re
import urllib
import gzip
import json


# ===============
# 定义常量和工具函数
# ===============
# 以下为选项默认值
DEFAULT_MAXIMUM_RESULTS = 20
DEFAULT_FILENAME_SHORTCUT = True
DEFAULT_CLEAN_AUTHORNAME = True

# 以下为URL模板
NDL_OPENSEARCH_BASE_URL = "https://ndlsearch.ndl.go.jp/api/opensearch"
OpensearchURLTemplate = (
    lambda maxium_results, isbn=None, title=None, author=None: "".join(
        [
            NDL_OPENSEARCH_BASE_URL,
            "?cnt={}".format(maxium_results),
            "&isbn={}".format(isbn) if isbn != None else "",
            "&title={}".format(title) if title != None else "",
            "&creator={}".format(author) if author != None else "",
        ]
    )
)

SEARCH_NDLBIBID_TEMPLATE = (
    "https://ndlsearch.ndl.go.jp/search?cs=bib&f-bibid={ndlbibid}"
)
NDL_EXPORT_JSON_TEMPLATE = (
    "https://ndlsearch.ndl.go.jp/api/bib/download/json?cs=bib&f-token={token}"
)
NDL_COVER_TEMPLATE = "https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg"

# 以下为默认请求头
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "max-age=0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
}


# 以下为生成元数据类的工厂函数
def MetadataFactory(book, log):
    mi = MetaInformation(book["title"], book["authors"])
    mi.identifiers = {
        "isbn": book.get("isbn", ""),
        "ndlbibid": book.get("ndlbibid", ""),
        "jpno": book.get("jpno", ""),
    }
    mi.publisher = book["publisher"]
    pubdate = book.get("pubdate", None)
    if pubdate:
        pubdate = ToHalfwidthNumber(pubdate)
        pubdate = re.sub(r"(\(.+\))|(（.+）)", "", pubdate)
        pubdate = pubdate[:-1] if not re.match(r"\d", pubdate[-1]) else pubdate
        try:
            if re.fullmatch(r"\d{4}\.\d{1,2}", pubdate):
                mi.pubdate = datetime.strptime(pubdate, "%Y.%m")
            elif re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}", pubdate):
                mi.pubdate = datetime.strptime(pubdate, "%Y.%m.%d")
            elif re.fullmatch(r"\d{4}", pubdate):
                mi.pubdate = datetime.strptime(pubdate, "%Y")
            else:
                raise ValueError
        except:
            log.error("出版日期解析失败，该日期形为{}".format(pubdate))
    mi.comments = book.get("description", "")
    mi.tags = book.get("tags", [])
    mi.isbn = book.get("isbn", "")
    mi.language = "ja"
    return mi


# 以下为将bs4的ResultSet转换为str列表的函数
def ToTextList(self):
    return [result.text for result in self]


# 添加到Result类当中作为方法，以便链式调用
ResultSet.toTextList = ToTextList


# 以下为全角数字转半角的函数
def ToHalfwidthNumber(text):
    translation_table = str.maketrans(
        {
            "０": "0",
            "１": "1",
            "２": "2",
            "３": "3",
            "４": "4",
            "５": "5",
            "６": "6",
            "７": "7",
            "８": "8",
            "９": "9",
        }
    )
    return text.translate(translation_table)


# ==========
# 检索逻辑部分
# ==========
class HonSagashi(Source):

    name = "日语图书元数据"
    author = "平方和寒"
    description = "一个专用于获取日文图书元数据的calibre插件。"
    version = (1, 0, 0)
    supported_platforms = ["windows", "osx", "linux"]

    capabilities = frozenset(["identify", "cover"])
    touched_fields = frozenset(
        [
            "pubdate",
            "title",
            "comments",
            "publisher",
            "authors",
            "language",
            "identifier:isbn",
            "identifier:jpno",
            "identifier:ndlbibid",
        ]
    )
    # 可以显示在calibre当中并进行配置的选项，包含以下内容
    # 名称、类型、默认值、标签、悬停提示
    # 类型包括'number', 'string', 'bool', 'choices'
    options = (
        Option(
            "max_results",
            "number",
            DEFAULT_MAXIMUM_RESULTS,
            ("最大检索结果数量"),
            ("NDL OpenSearch API支持的最高数量为500。"),
        ),
        Option(
            "filename_shortcut",
            "bool",
            DEFAULT_FILENAME_SHORTCUT,
            ("基于文件名的快速导入"),
            (
                "启用后可以直接在书名中以形如[NDLBibID]的形式书写，插件会自动读取ID下载元数据。"
            ),
        ),
        Option(
            "clean_authorname",
            "bool",
            DEFAULT_CLEAN_AUTHORNAME,
            ("净化人名"),
            ("自动去除人名中的空格、逗号以及数字"),
        ),
    )

    def __init__(self, *args, **kwargs):
        Source.__init__(self, *args, **kwargs)

    def identify(
        self,
        log,
        result_queue,
        abort,
        timeout=10,
        title=None,
        authors=None,
        identifiers={},
    ):

        self.timeout = timeout

        metadatas = []
        useShortcut = self.prefs.get("filename_shortcut")

        isbn = identifiers.get("isbn")
        if isbn:
            metadatas = self.acquireByISBN(isbn, log)
            log.info("基于ISBN获取元数据中, ISBN为{}".format(isbn))
            if len(metadatas) > 0:
                self.commitMetadata(metadatas, result_queue)
                return
        log.info("无isbn或未获取到信息")

        ndlbibid = identifiers.get("ndlbibid")
        # 支持提取书名中的[NDLBibID]
        if useShortcut and title and not ndlbibid:
            match = re.search(r"\[(\d+)\]", title)
            ndlbibid = match.groups(1) if match else None
        if ndlbibid:
            metadatas = self.acquireByNDLID(ndlbibid, log)
            log.info("基于NDLBibID获取元数据中，ID为{}".format(ndlbibid))
            if len(metadatas) > 0:
                self.commitMetadata(metadatas, result_queue)
                return
        log.info("无NDLBibID或未获取到信息")

        if title:
            if useShortcut:
                title = re.sub(r"\[(\d+)\]", "", title)
            metadatas = self.acquireByInfo(title, authors, log)
            log.info(
                "基于图书题名和作者获取元数据中，题为『{}』，作者为{}".format(
                    title, ";".join(authors)
                )
            )
            if len(metadatas) > 0:
                self.commitMetadata(metadatas, result_queue)
                return
        log.info("没有获取到任何结果")

    def acquireByISBN(self, isbn, log):
        queryURL = OpensearchURLTemplate(self.prefs.get("max_results"), isbn=isbn)
        response = urllib.request.urlopen(
            urllib.request.Request(queryURL, headers=HEADERS), timeout=self.timeout
        )
        bytedata = gzip.decompress(response.read())
        xmlText = bytedata.decode("utf-8")
        metadatas = self.parseXML(xmlText, log)
        return metadatas

    def acquireByInfo(self, title, authors, log):
        authorStr = " ".join(authors)
        quotedAuthor = urllib.parse.quote(authorStr, "utf-8")
        quotedTitle = urllib.parse.quote(title, "utf-8")
        queryURL = OpensearchURLTemplate(
            self.prefs.get("max_results"), title=quotedTitle, author=quotedAuthor
        )
        log.info(
            "已经进行转义，题名编码为{}，作者编码为{}".format(quotedTitle, quotedAuthor)
        )
        response = urllib.request.urlopen(
            urllib.request.Request(queryURL, headers=HEADERS), timeout=self.timeout
        )
        bytedata = gzip.decompress(response.read())
        xmlText = bytedata.decode("utf-8")
        metadatas = self.parseXML(xmlText, log)
        return metadatas

    def acquireByNDLID(self, ndlbibid, log):
        idSearchURL = SEARCH_NDLBIBID_TEMPLATE.format(ndlbibid=ndlbibid)
        response = urllib.request.urlopen(
            urllib.request.Request(idSearchURL, headers=HEADERS), timeout=self.timeout
        )
        bytedata = gzip.decompress(response.read())
        htmlText = bytedata.decode("utf-8")
        soup = BeautifulSoup(htmlText)
        # f-token的形式是'{dpid}-{ndlbibid}'
        # f-token用于对ndl search收录的数据进行唯一标识
        # 本处利用了ndl遗留的旧页面获取链接，链接末尾即为token
        token = (
            soup.find("div", {"class": "search-result-item"}).find("h3").find("a")["id"]
        )

        jsonApiURL = NDL_EXPORT_JSON_TEMPLATE.format(token=token)
        response = urllib.request.urlopen(
            urllib.request.Request(jsonApiURL, headers=HEADERS), timeout=self.timeout
        )
        # 注意导出的JSON不会经过gzip压缩，即使请求头中有相关内容
        bytedata = response.read()
        # if dict(response.headers).get('Content-Encoding') == 'gzip':
        #     bytedata = gzip.decompress(bytedata)
        jsonText = bytedata.decode("utf-8")
        jsonData = json.loads(jsonText)
        try:
            book = {
                "title": jsonData["title"][0]["value"],
                "authors": [creator["name"] for creator in jsonData["creator"]],
                "publisher": jsonData["publisher"][0]["name"],
                "pubdate": jsonData["date"],
                "description": "",
                "tags": [],
            }
        except KeyError:
            log.error("本条记录缺失关键字段，自动停止[使用的NDLBibID为{}]".format(ndlbibid))
            return

        if jsonData.get("identifier"):
            identifiers = jsonData["identifier"]
            book["jpno"] = identifiers.get("JPNO", [""])[0]
            book["ndlbibid"] = identifiers.get("NDLBibID", [""])[0]
            book["isbn"] = identifiers.get("ISBN", [""])[0]


        itemList = (
            jsonData["subject"].get("NDLSH", [])
            + jsonData["subject"].get("NDLC", [])
            + jsonData["subject"].get("NDL10", [])
        )
        for item in itemList:
            if "--" in item:
                book["tags"] += item.split("--")
            else:
                book["tags"] += [item]

        return [MetadataFactory(book, log)]

    def commitMetadata(self, metadatas, result_queue):
        if not isinstance(metadatas, list):
            raise TypeError("元数据结果不是列表，无法批量提交队列")
        for metadata in metadatas:
            self.postProcess(metadata)
            result_queue.put(metadata)

    def parseXML(self, xml, log):
        metadatas = []
        soup = BeautifulSoup(xml, features="xml")

        for item in soup.find_all("item"):
            try:
                book = {
                    "title": item.find("dc:title").text,
                    "authors": item.find_all("dc:creator").toTextList(),
                    "publisher": item.find("dc:publisher").text,
                    "pubdate": item.find("dcterms:issued").text,
                }
            except AttributeError:
                log.error("本条记录缺失关键字段，跳过")
                continue

            jpnoElement = soup.find("item").find(
                "dc:identifier", {"xsi:type": "dcndl:JPNO"}
            )
            book["jpno"] = jpnoElement.text if jpnoElement else ""
            ndlbibidElement = soup.find("item").find(
                "dc:identifier", {"xsi:type": "dcndl:NDLBibID"}
            )
            book["ndlbibid"] = ndlbibidElement.text if ndlbibidElement else ""
            isbnElement = soup.find("item").find(
                "dc:identifier", {"xsi:type": "dcndl:ISBN"}
            )
            book["isbn"] = isbnElement.text if isbnElement else ""

            tags = []
            for subject in item.find_all("dc:subject"):
                if "--" in subject.text:
                    tags += subject.text.split("--")
                else:
                    tags += [subject.text]
            book["tags"] = tags

            descriptions = item.find_all("dc:description").toTextList()
            descriptions += item.find_all("description").toTextList()
            print(descriptions)
            book["description"] = ""
            for description in descriptions:
                book["description"] += "<p>{}</p>".format(description)

            metadatas.append(MetadataFactory(book, log))

        return metadatas

    def postProcess(self, metadata: MetaInformation):
        if self.prefs.get("clean_authorname"):
            temp = []
            for author in metadata.authors:
                cleanname = re.sub(r"[\s\d,，]+", "", author)
                temp.append(cleanname)
            metadata.authors = temp

        return metadata

    def download_cover(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=10,
        get_best_cover=False,
    ):
        if "isbn" not in identifiers:
            return
        isbn = identifiers["isbn"].replace("-", "")
        coverURL = NDL_COVER_TEMPLATE.format(isbn=isbn)
        log.info("封面url为：", coverURL)
        try:
            coverData = self.browser.open_novisit(coverURL, timeout=timeout).read()
            result_queue.put((self, coverData))
        except Exception as e:
            if callable(getattr(e, "getcode", None)) and e.getcode() == 404:
                log.error("未能根据ISBN找到封面，放弃下载")
            else:
                log.exception("出错，基于ISBN获取封面失败")


# =======
# 测试用例
# =======
if __name__ == "__main__":
    from calibre.ebooks.metadata.sources.test import (
        test_identify_plugin,
        title_test,
        authors_test,
    )

    tests = [
        (
            {
                "identifiers": {"isbn": "9784121027504"},
            },
            [
                title_test("幕府海軍 : ペリー来航から五稜郭まで", exact=True),
                authors_test(["金澤裕之"]),
            ],
        ),
        # 要测试下面这一项，需要确认DEFAULT_FILENAME_SHORTCUT为True
        # (
        #     {
        #         'title': '近世後期の海防と社会変容[033336476]',
        #     },
        #     [
        #         title_test('近世後期の海防と社会変容', exact=True),
        #         authors_test(['清水詩織'])
        #     ]
        # )
    ]

    test_identify_plugin(HonSagashi.name, tests)
