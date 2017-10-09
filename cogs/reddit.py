import asyncio

from discord.ext import commands
import validators
import discord


class Reddit:

    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self.session = bot.session

        self.valid_url_endings = [
            '.jpg',
            '.png',
            '.gif'
        ]

        self.reddit_url = r'https://www.reddit.com'

        self.feed_data = {}
        self.old_feed = {}

        self.feed_checker = bot.loop.create_task(self.check_feeds())

        self.invalids = [
            'owner',
            'feeds'
        ]

    def __unload(self):
        self.feed_checker.cancel()

    async def check_feeds(self):
        while True:

            await asyncio.sleep(10)
            feeds = self.db.get('feeds', [])

            if not feeds:
                continue

            for subreddit in feeds:

                resp = await self.api_call(subreddit, 'new')
                if not resp['data']['children']:
                    continue

                subdata = resp['data']['children'][0]['data']

                subdata_dict = {
                    'subreddit' : subdata['subreddit_name_prefixed'].replace('\\', ''),
                    'name' : subdata['name'],
                    'title' : subdata['title'],
                    'url' : subdata['url'].replace('\\', ''),
                    'permalink' : self.reddit_url + subdata['permalink'].replace('\\', ''),
                    'author' : subdata['author'],
                    'nsfw' : subdata['over_18'],
                    'is_self' : subdata['is_self']
                }
                if subdata['is_self']:
                    subdata_dict['selftext'] = subdata['selftext'][:250]
                if subdata['thumbnail']:
                    subdata_dict['thumbnail'] = subdata['thumbnail']

                self.feed_data[subreddit] = subdata_dict

                sub = self.old_feed.get(subreddit, {})
                old_name = sub.get('name', '')
                sub = self.feed_data.get(subreddit, {})
                name = sub.get('name', '')

                embed = self.get_card_embed(self.feed_data[subreddit])

                for server_id in self.db.all():
                    if server_id in self.invalids:
                        continue

                    server_db = self.db.get(server_id, {})
                    server_feeds = server_db.get('feeds', {})
                    following = server_feeds.get('following', [])

                    if not server_feeds.get('channel'):
                        continue

                    channel_id = server_feeds['channel']

                    server_obj = discord.utils.get(self.bot.guilds, id=int(server_id))
                    if not server_obj:
                        continue
                    channel_obj = discord.utils.get(server_obj.text_channels, id=int(channel_id))
                    if not channel_obj:
                        continue

                    if subreddit in following and old_name != name:
                        await channel_obj.send(embed=embed)

            for sub in self.feed_data:
                self.old_feed[sub] = self.feed_data[sub]

    def get_card_embed(self, subdata : dict):
        embed = discord.Embed()
        embed.color = 0xe21fd9

        subreddit = subdata['subreddit']
        url = subdata['url']
        title = subdata['title']
        permalink = subdata['permalink']
        author_name = '/u/' + subdata['author']
        post_type = 'Self Post' if subdata['is_self'] else 'Link'

        embed.title = title
        embed.url = permalink
        if subdata['is_self']:
            selftext = subdata['selftext']
            embed.description = selftext + ' ...' if len(selftext) == 250 else selftext
        if 'thumbnail' in subdata and validators.url(subdata['thumbnail']):
            embed.set_thumbnail(url=subdata['thumbnail'])

        if url.endswith(tuple(self.valid_url_endings)) and not subdata['nsfw']:
            embed.set_image(url=url)

        embed.set_author(name=author_name + ' ⚪ ' + post_type, url=self.reddit_url + '/u/' + subdata['author'])

        embed.add_field(name='Subreddit', value=f'[{subreddit}]({self.reddit_url}/{subreddit})')

        if not subdata['is_self']:
            embed.add_field(name='URL', value=f'[Link]({url})')

        if subdata['nsfw']:
            embed.add_field(name='⚠ NSFW ⚠', value='Caution NSFW')

        return embed

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def reddit(self, ctx):
        """
        Watch/unwatch new posts from subreddits.

        Checks for new posts every 10 seconds.
        """

        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        server_feeds = server_db.get('feeds', {})
        channel = server_feeds.get('channel')
        following = server_feeds.get('following', [])

        embed = discord.Embed()
        embed.color = 0xe21fd9

        channel = discord.utils.get(guild.text_channels, id=int(channel))

        embed.title = 'Reddit'
        embed.description = f'**Channel for posts:** {channel}\n'
        embed.description += '**Currently watching:**\n'
        embed.description += '\n'.join(['/r/' + sub for sub in following])

        await ctx.send(embed=embed)

    async def feed_check(self):

        follow_lists = []
        for guild in self.bot.guilds:
            server_db = self.db.get(guild.id, {})
            server_feeds = server_db.get('feeds', {})
            follow_lists.append(server_feeds.get('following', []))

        feeds = self.db.get('feeds', [])

        for subreddit in feeds:
            if not(any(subreddit in l for l in follow_lists)):
                feeds.remove(subreddit)

        await self.db.put('feeds', feeds)

    @reddit.command(name='watch', aliases=['follow'])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def r_watch(self, ctx, subreddit):
        """Enables or disables watching new posts from a subreddit."""
        guild = ctx.guild
        subreddit = subreddit.lower()

        server_db = self.db.get(guild.id, {})
        server_feeds = server_db.get('feeds', {})
        following = server_feeds.get('following', [])

        feeds = self.db.get('feeds', [])
        if subreddit not in feeds:
            feeds.append(subreddit)

        if subreddit in following:
            following.remove(subreddit)

            server_feeds['following'] = following
            server_db['feeds'] = server_feeds
            await self.db.put(guild.id, server_db)

            await self.feed_check()

            await ctx.send(f'**No longer watching for new posts from:** /r/{subreddit}')
        else:
            await ctx.send(f'**Now watching for new posts from:** /r/{subreddit}')
            following.append(subreddit)

        server_feeds['following'] = following
        server_db['feeds'] = server_feeds

        await self.db.put('feeds', feeds)
        await self.db.put(guild.id, server_db)

    @reddit.command(name='mark')
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def r_mark(self, ctx):
        """Marks a channel to be used for new subreddit posts."""
        guild = ctx.guild

        server_db = self.db.get(guild.id, {})
        server_feeds = server_db.get('feeds', {})

        server_feeds['channel'] = ctx.channel.id

        server_db['feeds'] = server_feeds

        await self.db.put(guild.id, server_db)

        await ctx.send(f'Reddit feed update channel set to {ctx.channel.name}.')

    async def api_call(self, subreddit, sort):
        url = f'{self.reddit_url}/r/{subreddit}/{sort}.json'

        async with self.session.get(url) as rawdata:
            return await rawdata.json()

def setup(bot):
    bot.add_cog(Reddit(bot))
