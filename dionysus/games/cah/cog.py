import logging
import random
import discord
from discord.ext import commands
import emoji

from .game import CardsAgainstHumanity, GameState, Player, ANSWERS, QUESTIONS

logger = logging.getLogger(__name__)


class CardsAgainstHumanityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        # A reference to the bot client
        self.bot = bot
        # Games keyed by game id
        self.games = {}
        # Games keyed by player id
        self.players = {}

    def _build_hand_embed(self, game: CardsAgainstHumanity, player_id: int):
        player: Player = game.players[player_id]

        embed = discord.Embed(
            title="Cards Against Humanity",
            description=f"Choose your best answer to:\n> {game.question}\nSubmit your answer with `{self.bot.command_prefix}cah submit {' '.join('[id]' for i in range(game.question.pick))}`",
            color=0x00FFFF,
        )

        for i, answer in enumerate(player.hand):
            embed.add_field(name="{}".format(i + 1), value=str(answer), inline=False)

        return embed

    def _build_judge_embed(self, game: CardsAgainstHumanity):
        embed = discord.Embed(
            title="Cards Against Humanity",
            description=f"Choose the best answer to:\n{game.question}\nSelect the winner with `{self.bot.command_prefix}cah choose [id]`",
            color=0x00FFFF,
        )
        for i, submission_id in enumerate(game.submission_mapping):
            answer = game.submissions[submission_id]
            embed.add_field(
                name=f"{i + 1}", value=game.question.fill_in(answer), inline=False
            )

        return embed

    def _build_winner_embed(self, game: CardsAgainstHumanity):
        winner = game.get_winner_id()
        submissions = sorted(game.submissions, key=lambda x: game.players[x].name)
        embed = discord.Embed(
            title="Cards Against Humanity",
            description=f"{game.players[winner].name} is the winner!",
            color=0x00FFFF,
        )
        embed.add_field(
            name=emoji.emojize(f":star: {game.players[winner].name} :star:"),
            value=game.question.fill_in(game.submissions[winner]),
            inline=False,
        )
        for player_id in submissions:
            # Skip the winner
            if player_id == winner:
                continue
            embed.add_field(
                name=game.players[player_id].name,
                value=game.question.fill_in(game.submissions[player_id]),
                inline=False,
            )
        return embed

    def _build_score_embed(self, game: CardsAgainstHumanity):
        ranks = sorted(game.players, key=lambda id: game.players[id].score)
        score_list = []
        for id in ranks:
            player = game.players[id]
            score_list.append(f"{player.name} - {player.score}")
        scores = "\n".join(score_list)
        embed = discord.Embed(
            title="Cards Against Humanity",
            description=f"Scores after {game.round} rounds:\n{scores}",
            color=0x00FFFF,
        )
        return embed

    @commands.group()
    async def cah(self, ctx):
        # async def cah(ctx, user: discord.User = None):
        if ctx.invoked_subcommand is None:
            # user = user or ctx.author
            user = ctx.author
            if not ctx.guild:
                await ctx.send(
                    "Sorry {user.display_name}, you can only play this game inside a server.".format(
                        user=user
                    )
                )
                return False

            game = CardsAgainstHumanity()
            self.games[game.key] = {
                "guild": ctx.guild,
                "channel": ctx.channel,
                "game": game,
            }

            embed = discord.Embed(
                title="Cards Against Humanity",
                description="Fill in the blank using politically incorrect words or phrases.",
                color=0x00FFFF,
            )
            embed.set_footer(
                text="Game {game.key} created by {user.display_name}".format(
                    user=user, game=game
                )
            )
            embed.add_field(
                name="{prefix}cah join {key}".format(
                    prefix=self.bot.command_prefix, key=game.key
                ),
                value="to join",
                inline=True,
            )
            embed.add_field(
                name="{prefix}cah start {key}".format(
                    prefix=self.bot.command_prefix, key=game.key
                ),
                value="to start",
                inline=True,
            )

            await ctx.send(embed=embed)
            return True

    @cah.command()
    async def deal(self, ctx):
        hand = random.choices(ANSWERS, k=8)
        question = random.choice(QUESTIONS)
        embed = discord.Embed(
            title="Cards Against Humanity",
            description="Chose the best answer for\n\n> {}".format(question),
            color=0xFF0000,
        )
        for i, answer in enumerate(hand):
            embed.add_field(name=i, value=str(answer), inline=False)

        await ctx.send(embed=embed)

    @cah.command()
    async def join(self, ctx, key: str):
        if key not in self.games:
            pass
        user = ctx.author
        if user.id in self.players:
            pass
        ref = self.games[key]
        game = ref["game"]

        if game.add_player(Player(user.id, user.display_name)):
            self.players[user.id] = game.key
            await user.send(
                "Thanks for joining Cards Against Humanity game {game.key} in {guild.name} {channel.mention}.\nIt will start shortly.".format(
                    game=game, guild=ref["guild"], channel=ref["channel"]
                )
            )
        else:
            pass

    @cah.command()
    async def start(self, ctx):
        user = ctx.author
        if user.id not in self.players:
            pass

        key = self.players[user.id]
        if key not in self.games:
            pass
        ref = self.games[key]
        game = ref["game"]

        # The game requires you to be a member in order to start it
        if user.id not in game.players:
            await user.send(
                "You cannot start the Cards Against Humanity game {game.key} in {guild.name} {channel.mention} because you haven't joined it.".format(
                    game=game, guild=ref["guild"], channel=ref["channel"]
                )
            )
            return False
        # The game requires at least 3 players
        if len(game.players) < 3:
            await user.send(
                "You cannot start the Cards Against Humanity game {game.key} in {guild.name} {channel.mention} because it doesn't have enough players yet.".format(
                    game=game, guild=ref["guild"], channel=ref["channel"]
                )
            )
            return False

        # Start the game!
        embed = discord.Embed(
            title="Cards Against Humanity",
            description="Started by {user.display_name}!",
            color=0x00FFFF,
        )
        embed.set_footer(
            text="Cards Against Humanity game {game.key}".format(game=game)
        )
        await ref["channel"].send(embed=embed)
        return True

    @cah.command()
    async def submit(self, ctx, *args):
        user = ctx.author
        if user.id not in self.players:
            pass

        key = self.players[user.id]
        if key not in self.games:
            pass
        ref = self.games[key]
        game = ref["game"]

        if user.id not in game.players:
            pass
        player = game.players[user.id]

        answers = []
        for i in args:
            j = int(i)
            a = player.hand[j - 1]
            answers.append(a)

        logger.info("Submit: {}".format(answers))
        logger.info("Submit: {}".format(game.question.fill_in(answers)))
        if not game.submit_answer(player, answers):
            # handle submit failure
            return
        await user.send("You played:\n> {}".format(game.question.fill_in(answers)))

        # Check if the game is ready to judge
        if game.state == GameState.WAITING_FOR_JUDGE:
            await self._judging(game)

    async def _judging(self, game):
        embed = self._build_judge_embed(game)
        judge = self.bot.get_user(game.get_judge_id())
        await judge.send(embed=embed)

    @cah.command()
    async def choose(self, ctx, answer_id: int):
        user = ctx.author
        if user.id not in self.players:
            return

        key = self.players[user.id]
        if key not in self.games:
            return
        ref = self.games[key]
        game = ref["game"]

        if user.id is not game.get_judge_id():
            return

        game.choose_winner(answer_id - 1)
        if game.state == GameState.ROUND_COMPLETE:
            channel = ref["channel"]
            await channel.send(embed=self._build_winner_embed(game))
            await channel.send(embed=self._build_score_embed(game))

    @cah.command()
    async def debug(self, ctx):
        user = ctx.author
        if user.id not in self.players:
            pass

        key = self.players[user.id]
        if key not in self.games:
            pass
        ref = self.games[key]
        game = ref["game"]

        game.start_round()
        for player_id in game.players:
            user = self.bot.get_user(player_id)
            hand = self._build_hand_embed(game, player_id)
            await user.send(embed=hand)
