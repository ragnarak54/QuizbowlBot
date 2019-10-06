import discord
import reading
from discord.ext import commands
import asyncio

groups = []
teams = []
players = []


class Group:
    def __init__(self, name, members):
        self.name = name
        self.members = members


class Team:
    def __init__(self, server, name, captain, members, score=0):
        # self.group = group
        self.server = server
        self.name = name
        self.captain = captain
        self.members = members
        self.score = score

    def __str__(self):
        return self.name


class Player:
    def __init__(self, member, server, score=0):
        self.member = member
        self.server = server
        self.score = score  # not used for any data/analysis, just per-game score

    def __str__(self):
        return str(self.member.name)


def get_group(member):
    for group in groups:
        if member in group.members:
            return group
    return None


def get_team(member: discord.Member, server):
    for team in teams:
        for player in team.members:
            if member == player.member and server == player.server:
                return team
    return None


def get_player(member, server):
    for team in teams:
        for player in team.members:
            if member == player.member and server == player.server:
                return player


def serialize_team(teamname, server):
    for team in teams:
        if team.name == teamname and team.server == server:
            return team


class Tournament(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='group')
    async def group_(self, ctx, name):
        if any(each_group.name == name for each_group in groups):
            await ctx.send("That group already exists!")
            return
        groups.append(Group(name, [ctx.author]))
        await ctx.send(f'New group "{name}" created! Type !join {name} to join!')

    @commands.command()
    async def mygroup(self, ctx):
        group = get_group(ctx.author)
        if group is not None:
            await ctx.send(group.name)
        else:
            await ctx.send("You're not in a team.")

    @commands.command(name="team", aliases=["maketeam", "newteam"])
    async def team_(self, ctx, name):
        if any(each_team.name == name for each_team in teams):
            await ctx.send("That team already exists!")
            return
        if get_team(ctx.author, ctx.guild) is not None:
            await ctx.send("You're already in a team.")
            return
        else:
            player = Player(ctx.author, ctx.guild)
            players.append(player)
        team = Team(ctx.guild, name, ctx.author, [])
        team.members.append(player)
        print(player)
        teams.append(team)
        if ctx.author.nick:
            await ctx.send(
                f'''New team "{name}" created! Type !join {name} to join {ctx.author.nick}'s team!''')
        else:
            await ctx.send(
                f'''New team "{name}" created! Type !join {name} to join {ctx.author.name}'s team!''')

    @commands.command(name="teams", aliases=["listteams", "allteams"])
    async def teams_(self, ctx):
        teams_in_server = [team for team in teams if team.server == ctx.guild]
        if teams_in_server:
            team_list = f'Current teams in {ctx.guild}:\n' + ''.join(
                sorted(':small_blue_diamond:' + team.name + '\n' for team in teams_in_server))
            await ctx.send(team_list)
        else:
            await ctx.send("No teams have been made in this server yet!")

    @commands.command()
    async def myteam(self, ctx):
        team = get_team(ctx.author, ctx.guild)
        if team is not None:
            await ctx.send(team.name)
        else:
            await ctx.send("You're not in a team.")

    @commands.command(name="captain")
    async def captain_(self, ctx, new_captain: discord.Member = None):
        team = get_team(ctx.author, ctx.guild)
        if team is not None:
            if new_captain is None:
                await ctx.send(f"{team.captain.nick if team.captain.nick else team.captain.name} "
                               f"is the captain of your team, {team.name}")
                return
            if team.captain == ctx.author:
                if get_player(new_captain, ctx.guild) in team.members:
                    team.captain = new_captain
                    await ctx.send(f"New team captain of {team.name}: {new_captain}")
                else:
                    await ctx.send(f"{new_captain} isn't in your team!")
            else:
                await ctx.send(f"You aren't captain of {team.name}")
        else:
            await ctx.send("You're not in a team!")

    @commands.command()
    async def join(self, ctx, name):
        if get_player(ctx.author, ctx.guild) is not None:
            await ctx.send("You're already in a team. Leave your team first if you want to join another one.")
            return
        for team in teams:
            if team.name == name:
                player = Player(ctx.author, ctx.guild)
                team.members.append(player)
                author = ctx.author
                await ctx.send(f"{author.nick if author.nick else author.name} joined the team {name}!")
                return
        await ctx.send("That doesn't seem to be a team!")

    @commands.command(aliases=['leaveteam'])
    async def leave(self, ctx, name=None):
        member_team = get_team(ctx.author, ctx.guild)
        print(member_team)
        if name is None:
            if member_team is None:
                await ctx.send("You're not in a team.")
                return

        if member_team is not None and (member_team.name == name or name is None):
            if len(member_team.members) == 1:
                await ctx.send(
                    "You're the last person in the team!\nLeaving the team has deleted it. You can always create "
                    "a new one with !team <team name>.")
                teams.remove(member_team)
                return
            if ctx.author == member_team.captain:
                await ctx.send(
                    f"You're the captain of {member_team}! You should defer captainship to one of your teammates with "
                    f"!captain @user.\nTeam members:\n" + "".join(
                        [":small_blue_diamond:" + str(member) + "\n" for member in member_team.members]))
                return
            member_team.members.remove(get_player(ctx.author, ctx.guild))
            await ctx.send(f"Left {name}!")
            return

        await ctx.send("You're not in a team by that name.")

    @commands.command()
    async def tournament(self, ctx, *, teams_in_game=None):
        bot = self.bot
        caller_team = get_team(ctx.author, ctx.guild)
        if caller_team is None:
            await ctx.send("You should make or join a team first.")
            return
        if caller_team.captain != ctx.author:
            await ctx.send("You can't start a tournament unless you're a team captain.")
            return
        if teams_in_game is None:
            teams_in_game = [x for x in teams if x.server == ctx.guild]
            for x in teams_in_game:
                x.score = 0
            string = 'Starting tournament with:\n' + "".join(
                [f':small_blue_diamond: {x.name} \n' for x in teams_in_game])
            await ctx.send(string)
        else:
            team_names = teams_in_game.split(" ")
            if len(team_names) < 2:
                await ctx.send("You must have at least 2 teams to have a tournament!")
                return
            teams_in_game = []
            for teamname in team_names:
                teams_in_game.append(serialize_team(teamname, ctx.guild))
            for team in teams_in_game:
                if team is None:
                    await ctx.send("Make sure to check your spelling! Teams currently in this server are:\n"
                                   + "".join([":small_blue_diamond:" + t_.name + "\n" for t_ in teams]))
                    return

        await ctx.send("Would you like bonus questions? Answer with yes or no.")
        msg = await self.bot.wait_for('message', check=lambda x: x.author == ctx.author)
        if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
            bonus = True
            await ctx.send("Bonus questions will be read.")
        else:
            bonus = False
            await ctx.send("Bonus questions will not be read.")
        await ctx.send("How many tossup questions do you want (default is 20)?")
        msg = await bot.wait_for('message', check=lambda x: x.author == ctx.author)
        num_of_questions = int(msg.content)
        if num_of_questions > 50:
            num_of_questions = 50
        await ctx.send("Tournament starting! Your setup is as follows:\n"
                       "Teams competing: " + ", ".join([t_.name for t_ in teams_in_game]) +
                       f"\nNumber of tossups: {num_of_questions} (maximum for a tourament)" +
                       f"\nBonus questions: {bonus}" +
                       "\nIf this is correct, type yes. "
                       "If you'd like to edit something, type teams, tossups, or bonuses.")

        def check2(message):
            return message.content.lower() in ["yes", "y", "ye", "yeet", "teams", "tossups",
                                               "bonuses"] and message.author == ctx.author

        msg = await bot.wait_for('message', check=check2)
        if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
            await ctx.send("Tournament starting! Good luck!")
        elif msg.content.lower() == "teams":
            await ctx.send("Alright, re-enter the list of teams competing, separated by spaces")
            msg = await bot.wait_for('message', check=lambda x: x.author == ctx.author)
            teams_in_game = msg.content.split(" ")
            if teams_in_game.count() < 2:
                await ctx.send("You must have at least 2 teams to have a tournament!")
                return
            for team in teams_in_game:
                if team not in [t.name for t in teams]:
                    await ctx.send("Make sure to check your spelling! Teams currently "
                                   "in this server are:\n"
                                   + "".join([":small_blue_diamond:" + t_.name + "\n" for t_ in teams]))
                    return
        elif msg.content.lower() == "tossups":
            await ctx.send("Alright, re-enter the number of tossups you want.")
            msg = await bot.wait_for('message', check=lambda x: x.author == ctx.author)
            num_of_questions = int(msg.content)
        elif msg.content.lower() == "bonuses":
            await ctx.send("Alright, re-renter yes or no if you want bonuses or not.")
            msg = await bot.wait_for('message', check=lambda x: x.author == ctx.author)
            if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
                bonus = True
                await ctx.send("Bonus questions will be read.")
            else:
                bonus = False
                await ctx.send("Bonus questions will not be read.")
        playerlist = []
        for t in teams_in_game:
            print(t.members)
            playerlist += t.members
        print(playerlist)
        for i in range(num_of_questions):
            await ctx.send(f"Tossup {i + 1} of {num_of_questions}:")
            await asyncio.sleep(1)
            await reading.tossup(bot, ctx.channel, bonus, playerlist)

        teams_in_game.sort(reverse=True, key=lambda x: x.score)
        await ctx.send("Tournament over! Final leaderboard:\n" +
                       "".join([":small_blue_diamond:" + t.name + ": " + str(t.score) + " points!\n" for t in
                                teams_in_game]))

    @commands.command(aliases=['s'])
    async def score(self, ctx):
        team = get_team(ctx.author, ctx.guild)
        player = get_player(ctx.author, ctx.guild)
        if team:
            await ctx.send(f"Your team has {team.score} points!\n"
                           f"You've scored {player.score} of them.")

    @commands.command()
    async def scores(self, ctx):
        scores = ""
        for team in [x for x in teams if x.server == ctx.guild]:
            scores += f':small_blue_diamond:{team.name}: {team.score} points\n'
        await ctx.send(scores)
