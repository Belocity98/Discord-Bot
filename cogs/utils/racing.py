import discord
import asyncio
import datetime

from random import randint

class Racing:

    def __init__(self, bot, message : discord.Message, users : list):
        self.bot = bot

        self.users = users

        self.message = message
        self.channel = message.channel

        self.rand_step = 3
        self.track_length = 30

        self.positions = {}
        self.tracks = {}

        self.active = False

    def get_track_embed(self):
        """Gets the inital embed for the track."""

        embed = discord.Embed()
        embed.color = 0x019608

        embed.title = 'Horse Racing'

        track = ''
        for i in range(self.track_length):
            track += '-'

        for i, user in enumerate(self.users):
            name = f'{user.name}\'s Horse'

            track_list = list(track)
            track_list[0] = '\N{HORSE RACING}'

            track = ''.join(track_list)

            embed.add_field(name=name, value='|' + track + '|')
            self.tracks[user.id] = track
            self.positions[user.id] = 0

        return embed

    async def move_horse(self, index):
        """Randomly moves a horse on the track."""

        uid = list(self.positions.keys())[index]

        user = discord.utils.get(self.message.guild.members, id=uid)
        name = f'{user.name}#{user.discriminator}\'s Horse'

        old_pos = self.positions[uid]

        step = randint(-1, self.rand_step)

        self.positions[uid] += step

        if self.positions[uid] < 0:
            self.positions[uid] = 0

        new_pos = self.positions[uid]

        track_list = list(self.tracks[uid])

        track_list[old_pos] = '-'

        try:
            track_list[new_pos] = '\N{HORSE RACING}'
        except IndexError:
            new_pos = self.track_length - 1
            track_list[new_pos] = '\N{HORSE RACING}'

        self.tracks[uid] = ''.join(track_list)

        return self.tracks[uid]

    async def start_racing(self):
        """Sends the racetrack and begins the race."""

        em = self.get_track_embed()
        self.game_board = await self.channel.send(embed=em)

        self.starttime = datetime.datetime.now()

        self.active = True

    async def check_for_winner(self):
        """Checks all the horses for a winner."""

        winners = []

        for uid, pos in self.positions.items():
            if pos >= self.track_length-1:
                winners.append(uid)

        return winners

    async def end_racing(self, winners : list):
        """End the race when somebody wins."""

        self.active = False
        endtime = datetime.datetime.now()

        delta = endtime - self.starttime
        seconds = round(delta.total_seconds(), 2)

        members = self.message.guild.members
        winner_objs = [discord.utils.get(members, id=uid) for uid in winners]

        winner_names = [m.name for m in winner_objs]

        await self.game_board.delete()
        await self.channel.send(content=f'{seconds} seconds\nWinner(s): ' + ', '.join(winner_names))

    async def update_track(self):
        """Updates the track."""

        embed = self.game_board.embeds[0]

        for i, field in enumerate(embed.fields):
            val = await self.move_horse(i)

            embed.set_field_at(i, name=field.name, value='|' + val + '|')

        await self.game_board.edit(content=' ', embed=embed)

    async def start(self):
        """Handles the loop for the race."""

        await self.start_racing()

        while self.active:
            await asyncio.sleep(3)
            await self.update_track()
            winners = await self.check_for_winner()
            if winners:
                await self.end_racing(winners)
