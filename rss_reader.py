import datetime
import sqlite3
from dataclasses import dataclass
from typing import List
import feedparser


@dataclass
class FeedEntry:
    title: str
    link: str
    description: str
    published: str
    feed_title: str


class RSSReader:
    def __init__(self, db_path: str = "rss_feeds.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库，创建必要的表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 创建订阅源表
        c.execute('''
            CREATE TABLE IF NOT EXISTS feeds
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             url TEXT UNIQUE,
             title TEXT,
             last_updated TIMESTAMP)
        ''')

        # 创建文章表
        c.execute('''
            CREATE TABLE IF NOT EXISTS entries
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             feed_id INTEGER,
             title TEXT,
             link TEXT UNIQUE,
             description TEXT,
             published TIMESTAMP,
             FOREIGN KEY (feed_id) REFERENCES feeds (id))
        ''')

        conn.commit()
        conn.close()

    def add_feed(self, url: str) -> bool:
        """添加新的订阅源"""
        try:
            # 验证并获取feed信息
            feed = feedparser.parse(url)
            if feed.bozo:  # 检查feed是否有效
                print(f"无效的Feed URL: {url}")
                return False

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # 插入feed信息
            c.execute(
                "INSERT OR IGNORE INTO feeds (url, title, last_updated) VALUES (?, ?, ?)",
                (url, feed.feed.title, datetime.datetime.now())
            )

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"添加feed时发生错误: {str(e)}")
            return False

    def update_feeds(self) -> List[FeedEntry]:
        """更新所有订阅源的内容"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # 获取所有订阅源
        c.execute("SELECT id, url, title FROM feeds")
        feeds = c.fetchall()

        new_entries = []
        for feed_id, feed_url, feed_title in feeds:
            try:
                # 解析feed
                feed = feedparser.parse(feed_url)

                # 处理每个文章
                for entry in feed.entries:
                    # 尝试获取发布时间
                    published = entry.get('published', entry.get('updated', ''))

                    # 创建新的文章记录
                    c.execute("""
                        INSERT OR IGNORE INTO entries 
                        (feed_id, title, link, description, published)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        feed_id,
                        entry.get('title', '无标题'),
                        entry.get('link', ''),
                        entry.get('description', ''),
                        published
                    ))

                    if c.rowcount > 0:  # 如果插入了新记录
                        new_entries.append(FeedEntry(
                            title=entry.get('title', '无标题'),
                            link=entry.get('link', ''),
                            description=entry.get('description', ''),
                            published=published,
                            feed_title=feed_title
                        ))

                # 更新最后更新时间
                c.execute(
                    "UPDATE feeds SET last_updated = ? WHERE id = ?",
                    (datetime.datetime.now(), feed_id)
                )

            except Exception as e:
                print(f"更新feed {feed_url} 时发生错误: {str(e)}")
                continue

        conn.commit()
        conn.close()
        return new_entries

    def get_recent_entries(self, limit: int = 50) -> List[FeedEntry]:
        """获取最近的文章"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT e.title, e.link, e.description, e.published, f.title
            FROM entries e
            JOIN feeds f ON e.feed_id = f.id
            ORDER BY e.published DESC
            LIMIT ?
        """, (limit,))

        entries = [
            FeedEntry(
                title=row[0],
                link=row[1],
                description=row[2],
                published=row[3],
                feed_title=row[4]
            )
            for row in c.fetchall()
        ]

        conn.close()
        return entries

    def format_feed_entry(self, entry: FeedEntry) -> str:
        """将FeedEntry格式化为字符串"""
        fields = [
            f"标题: {entry.title}",
            f"来源: {entry.feed_title}" if entry.feed_title else None,
            f"链接: {entry.link}",
            f"发布时间: {entry.published}" if entry.published else None
        ]
        # 过滤掉None值，只保留有效字段
        valid_fields = [field for field in fields if field is not None]
        return "\n".join(valid_fields)


def main():
    # 使用示例
    reader = RSSReader()

    # 添加一些RSS源
    feeds = [
        "https://news.ycombinator.com/rss",
        "http://feeds.feedburner.com/PythonInsider"
    ]

    for feed_url in feeds:
        if reader.add_feed(feed_url):
            print(f"成功添加: {feed_url}")

    # 更新所有feed
    print("\n更新订阅源...")
    new_entries = reader.update_feeds()

    # 打印新文章
    print(f"\n获取到 {len(new_entries)} 条新文章:")
    for entry in new_entries:
        print(f"\n标题: {entry.title}")
        print(f"来源: {entry.feed_title}")
        print(f"链接: {entry.link}")
        print(f"发布时间: {entry.published}")
        print("-" * 50)


if __name__ == "__main__":
    main()
