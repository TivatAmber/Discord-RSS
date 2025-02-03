import discord
from discord.ext import commands
from rss_reader import RSSReader
import json

def load_config():
    """
    从 config.json 加载配置
    返回 Discord 机器人令牌
    """
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("错误: 找不到 config.json 文件")
        return None
    except json.JSONDecodeError:
        print("错误: config.json 格式不正确")
        return None
    except KeyError:
        print("错误: config.json 中缺少必要的配置项")
        return None

# 配置机器人
config = load_config()
intents = discord.Intents.default()
intents.message_content = True
if config['proxy'] is None or config['proxy'] == "":
    bot = commands.Bot(command_prefix='!', intents=intents)
else:
    bot = commands.Bot(command_prefix='!', intents=intents, proxy=config['proxy'])
reader = RSSReader()


# Bot 准备就绪事件
@bot.event
async def on_ready():
    print(f'Bot已登录为 {bot.user}')


# 定义一个自定义消息命令
@bot.command(name='announce')
async def announce(ctx):
    """当用户输入 !announce 时，机器人会发送一条特定的公告"""
    announcement = """
    📢 重要公告！
    欢迎来到我们的 Discord 服务器！
    
    - 请阅读服务器规则
    
    - 善待其他成员
    
    - 玩得开心！
    """
    await ctx.send(announcement)


# 定义一个自定义消息命令
@bot.command(name='rss')
async def rss_send(ctx):
    """当用户输入 !rss 时，机器人会发送rss订阅信息"""
    print("\n更新订阅源...")
    new_entries = reader.update_feeds()
    print(f"\n获取到 {len(new_entries)} 条新文章:")
    for entry in reversed(new_entries):
        msg = reader.format_feed_entry(entry)
        await ctx.send(msg)


# 错误处理
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("抱歉，我不认识这个命令。请使用 !help 查看所有可用命令。")
    else:
        await ctx.send(f"执行命令时发生错误: {str(error)}")


# 运行机器人
def main():
    for feed_url in config['rss']['feeds']:
        if reader.add_feed(feed_url):
            print(f"成功添加: {feed_url}")
    # 从配置文件加载令牌
    TOKEN = config["token"]["discord"]
    if TOKEN is None:
        print("无法启动机器人：配置加载失败")
        return

    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("登录失败：请检查你的机器人令牌是否正确")
    except Exception as e:
        print(f"启动时发生错误: {str(e)}")


if __name__ == "__main__":
    main()