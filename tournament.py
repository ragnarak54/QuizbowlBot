import discord
import main
from discord.ext import commands
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


class Tournament:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='group', pass_context=True)
    async def group_(self, ctx, name):
        bot = self.bot
        if any(each_group.name == name for each_group in groups):
            await self.bot.say("That group already exists!")
            return
        groups.append(Group(name, [ctx.message.author]))
        await bot.say('New group "{0}" created! Type !join {0} to join!'.format(name))

    @commands.command(pass_context=True)
    async def mygroup(self, ctx):
        group = self.get_group(ctx.message.author)
        if group is not None:
            await self.bot.say(group.name)
        else:
            await self.bot.say("You're not in a team.")

    @commands.command(name="team", pass_context=True, aliases=["maketeam", "newteam"])
    async def team_(self, ctx, name):
        if any(each_team.name == name for each_team in teams):
            await self.bot.say("That team already exists!")
            return
        if self.get_team(ctx.message.author, ctx.message.server) is not None:
            await self.bot.say("You're already in a team.")
            return
        else:
            player = Player(ctx.message.author, ctx.message.server)
            players.append(player)
        team = Team(ctx.message.server, name, ctx.message.author, [])
        team.members.append(player)
        print(player)
        teams.append(team)
        await self.bot.say('New team "{0}" created! Type !join {0} to join!'.format(name))

    @commands.command(name="teams", pass_context=True, aliases=["listteams", "allteams"])
    async def teams_(self, ctx):
        teams_in_server = [team for team in teams if team.server == ctx.message.server]
        if teams_in_server:
            team_list = 'Current teams in {0}:\n'.format(ctx.message.server) + ''.join(
                sorted(':small_blue_diamond:' + team.name + '\n' for team in teams_in_server))
            await self.bot.say(team_list)
        else:
            await self.bot.say("No teams have been made in this server yet!")

    @commands.command(pass_context=True)
    async def myteam(self, ctx):
        team = self.get_team(ctx.message.author, ctx.message.server)
        if team is not None:
            await self.bot.say(team.name)
        else:
            await self.bot.say("You're not in a team.")

    @commands.command(name="captain", pass_context=True)
    async def captain_(self, ctx, new_captain: discord.Member = None):
        team = self.get_team(ctx.message.author, ctx.message.server)
        if team is not None:
            if new_captain is None:
                await self.bot.say("{0} is the captain of your team, {1}".format(team.captain, team.name))
                return
            if team.captain == ctx.message.author:
                if self.get_player(new_captain, ctx.message.server) in team.members:
                    team.captain = new_captain
                    await self.bot.say("New team captain of {0}: {1}".format(team, new_captain))
                else:
                    await self.bot.say("{0} isn't in your team!".format(new_captain))
            else:
                await self.bot.say("You aren't captain of {0}".format(team.name))
        else:
            await self.bot.say("You're not in a team!")

    @commands.command(pass_context=True)
    async def join(self, ctx, name):
        if self.get_player(ctx.message.author, ctx.message.server) is not None:
            await self.bot.say("You're already in a team. Leave your team first if you want to join another one.")
            return
        for team in teams:
            if team.name == name:
                player = Player(ctx.message.author, ctx.message.server)
                team.members.append(player)
                await self.bot.say("{0} joined the team {1}!".format(ctx.message.author, name))
                return
        await self.bot.say("That doesn't seem to be a team!")

    @commands.command(pass_context=True, aliases=['leaveteam'])
    async def leave(self, ctx, name=None):
        member_team = self.get_team(ctx.message.author, ctx.message.server)
        if name is None:
            if member_team is None:
                await self.bot.say("You're not in a team.")
                return

        if member_team is not None and (member_team.name == name or name is None):
            if len(member_team.members) == 1:
                await self.bot.say(
                    "You're the last person in the team!\nLeaving the team has deleted it. You can always create "
                    "a new one with !team <team name>.")
                teams.remove(member_team)
                return
            if ctx.message.author == member_team.captain:
                await self.bot.say(
                    "You're the captain of {0}! You should defer captainship to one of your teammates with !captain @user.\nTeam members:\n".format(
                        member_team) + "".join(
                        [":small_blue_diamond:" + str(member) + "\n" for member in member_team.members]))
                return
            member_team.members.remove(self.get_player(ctx.message.author, ctx.message.server))
            await self.bot.say("Left {0}!".format(name))
            return

        await self.bot.say("You're not in a team by that name.")

    @commands.command(pass_context=True)
    async def tournament(self, ctx, *, teams_in_game=None):
        bot = self.bot
        caller_team = self.get_team(ctx.message.author, ctx.message.server)
        if caller_team is None:
            await self.bot.say("You should make or join a team first.")
            return
        if caller_team.captain != ctx.message.author:
            await self.bot.say("You can't start a tournament unless you're a team captain.")
            return
        if teams_in_game is None:
            await self.bot.say("Please enter the teams that will be playing in this tournament, "
                          "separated by spaces")
            msg = await self.bot.wait_for_message(author=ctx.message.author)
            team_names = msg.content.split(" ")
        else:
            team_names = teams_in_game.split(" ")
        if len(team_names) < 2:
            await self.bot.say("You must have at least 2 teams to have a tournament!")
            return
        teams_in_game = []
        for teamname in team_names:
            teams_in_game.append(self.serialize_team(teamname, ctx.message.server))
        for team in teams_in_game:
            if team not in teams:
                await self.bot.say("{0} isn't a team. Make sure to check your spelling! Teams currently "
                              "in this server are:\n".format(team)
                              + "".join([":small_blue_diamond:" + t_.name + "\n" for t_ in teams]))
                return

        await self.bot.say("Would you like bonus questions? Answer with yes or no.")
        msg = await self.bot.wait_for_message(author=ctx.message.author)
        if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
            bonus = True
            await self.bot.say("Bonus questions will be read.")
        else:
            bonus = False
            await self.bot.say("Bonus questions will not be read.")
        await bot.say("How many tossup questions do you want (default is 20)?")
        msg = await bot.wait_for_message(author=ctx.message.author)
        num_of_questions = int(msg.content)
        await bot.say("Tournament starting! Your setup is as follows:\n"
                      "Teams competing: " + ", ".join([t_.name for t_ in teams_in_game]) +
                      "\nNumber of tossups: " + str(num_of_questions) +
                      "\nBonus questions: " + str(bonus) +
                      "\nIf this is correct, type yes. If you'd like to edit something, type teams, tossups, or bonuses.")

        def check2(message):
            return message.content in ["yes", "y", "ye", "yeet", "teams", "tossups", "bonuses"]

        msg = await bot.wait_for_message(author=ctx.message.author, check=check2)
        if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
            await bot.say("Tournament starting! Good luck!")
        elif msg.content.lower() == "teams":
            await bot.say("Alright, re-enter the list of teams competing, separated by spaces")
            msg = await bot.wait_for_message(author=ctx.message.author)
            teams_in_game = msg.content.split(" ")
            if teams_in_game.count() < 2:
                await bot.say("You must have at least 2 teams to have a tournament!")
                return
            for team in teams_in_game:
                if team not in [t.name for t in teams]:
                    await bot.say("{0} isn't a team. Make sure to check your spelling! Teams currently "
                                  "in this server are:\n".format(team)
                                  + "".join([":small_blue_diamond:" + t_.name + "\n" for t_ in teams]))
                    return
        elif msg.content.lower() == "tossups":
            await bot.say("Alright, re-enter the number of tossups you want.")
            msg = await bot.wait_for_message(author=ctx.message.author)
            num_of_questions = int(msg.content)
        elif msg.content.lower() == "bonuses":
            await bot.say("Alright, re-renter yes or no if you want bonuses or not.")
            msg = await bot.wait_for_message(author=ctx.message.author)
            if msg.content.lower() in ["yes", "y", "ye", "yeet"]:
                bonus = True
                await bot.say("Bonus questions will be read.")
            else:
                bonus = False
                await bot.say("Bonus questions will not be read.")
        playerlist = []
        for t in teams_in_game:
            print(t.members)
            playerlist += t.members
        print(playerlist)
        for i in range(num_of_questions):
            await main.read_question(bonus, playerlist)
        teams_in_game.sort(reverse=True, key=lambda x: x.score)
        await bot.say("Tournament over! Final leaderboard:\n" +
                      "".join([":small_blue_diamond:" + t.name + ": " + str(t.score) + " points!\n" for t in
                               teams_in_game]))


def setup(bot):
    bot.add_cog(Tournament(bot))
