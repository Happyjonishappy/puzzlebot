import re
import asyncio
import random
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.commands import has_any_role

bold = lambda s: "**" + s + "**"

EMBED_COLOUR = 0xde3e61
ADMIN_EMBED_COLOUR = 0xf7c648

DELAY_AFTER_FAILING = 10
HUNT_ROLE = "Puzzle Hunter"
HUNT_ADMIN_ROLE = "Hunt Admin"
HUNT_HELP_ROLE = "Hunt Help"
HUNT_CATEGORY = "Team Channels"
HUNT_MAIN_CHANNEL = "hunt-channel"
HINT_CHANNEL = 'hint-channel'

class TextStringKey:
    REGISTER_CLARIFICATION = 'Register Clarification'
    ANSWER_CLARIFICATION = 'Answer Clarification'
    PUZZLE_ID_NOT_AVAILABLE = 'Puzzle ID Not Available'
    RECRUIT_CLARIFICATION = 'Recruit Clarification'
    NO_HUNT_RUNNING = 'No Hunt Running'
    TEAM_EXISTS = 'Team Exists'
    ADDING_RECRUIT = 'Adding Recruit'
    TEAM_NAME_LENGTH = 'Team Name Length'
    TEAM_NAME_FORMAT = 'Team Name Format'
    CREATED_TEAM = 'Created Team'
    NOT_IN_A_TEAM = 'Not in a Team'
    ALREADY_IN_A_TEAM = 'Already in a Team'
    WAITING_FOR_RECRUITEE = 'Waiting for Recruitee'
    RECRUITEE_IN_TEAM = 'Recruitee in Team'
    CORRECT_ANSWER = 'Correct Answer'
    WRONG_ANSWER = 'Wrong Answer'
    WRONG_CHANNEL = 'Wrong Channel'
    ALREADY_SOLVED = 'Already Solved'
    ATTEMPTING_TOO_SOON = 'Attempting Too Soon'
    HUNT_NOT_STARTED = 'Hunt Not Started'
    MISSING_VARIABLE = 'Missing Variable'
    START_HUNT_INTRO_HEADER = "Start Hunt Intro Header"
    START_HUNT_INTRO_TEXT = "Start Hunt Intro Text"
    FINISH_HUNT_OUTRO_HEADER = "Finish Hunt Outro Header"
    FINISH_HUNT_OUTRO_TEXT = "Finish Hunt Outro Text"
    NO_HINTS_AVAILABLE = "No Hints Available"
    HINT_INSTRUCTION = "Hint Instruction"
    HINT_TOO_SHORT = "Hint Too Short"
    YOU_GAVE_HINTS = "You Gave Hints"


def strfdelta(tdelta):
    hrs, rem = divmod(tdelta, 3600)
    mins, secs = divmod(rem, 60)
    f = ""
    if hrs:
        f = "%02d hours, " % (hrs)
    return f + "%02d minutes, %02d seconds" % (mins, secs)

class PuzzleHunt(commands.Cog):
    """
    Cog for puzzle hunt
    """
    # Variables
    DATABASE_SCHEMA = 'puzzledb'

    TEXT_STRINGS = {
    }

    LEADERBOARD_SQL = """
        SELECT teamsolves.teamname AS teamname, COALESCE(SUM(puzzles.points), 0) AS total_points, MAX(teamsolves.last_solvetime) AS last_solvetime FROM
            (SELECT teams.id AS teamid, teams.teamname AS teamname, MAX(solves.solvetime) 
                AS last_solvetime, solves.puzzleid as puzzleid, teams.huntid AS huntid FROM puzzledb.puzzlehunt_teams teams
            LEFT JOIN puzzledb.puzzlehunt_solves solves
                ON solves.teamid = teams.id AND solves.huntid = teams.huntid
                GROUP BY teams.id, solves.puzzleid) teamsolves
        LEFT JOIN puzzledb.puzzlehunt_puzzles puzzles
            ON teamsolves.puzzleid = puzzles.puzzleid AND teamsolves.huntid = puzzles.huntid
            WHERE teamsolves.huntid = %s
            GROUP BY teamsolves.teamid, teamsolves.teamname
            ORDER BY total_points DESC, last_solvetime ASC;
        """

    TEAM_INFO_SQL = """
        SELECT teamsolves.teamid AS teamid, teamsolves.teamname AS teamname, 
            MAX(teamsolves.last_solvetime) AS last_solvetime, COALESCE(SUM(puzzles.points), 0) AS total_points,
            teamsolves.teamchannel AS teamchannel, teamsolves.teamvoicechannel AS teamvoicechannel,
            teamsolves.teamhintcount AS teamhintcount FROM
                (SELECT teams.id AS teamid, teams.teamname AS teamname, MAX(solves.solvetime) AS last_solvetime, solves.puzzleid as puzzleid,
                    teams.huntid AS huntid, teams.teamchannel AS teamchannel, teams.teamvoicechannel AS teamvoicechannel, teams.hintcount AS teamhintcount FROM {0}.puzzlehunt_teams teams
                LEFT JOIN {0}.puzzlehunt_solves solves
                    ON solves.teamid = teams.id AND solves.huntid = teams.huntid
                    GROUP BY teams.id, solves.puzzleid) teamsolves
        LEFT JOIN {0}.puzzlehunt_puzzles puzzles
        ON teamsolves.puzzleid = puzzles.puzzleid AND teamsolves.huntid = puzzles.huntid
        WHERE teamsolves.huntid = %s and teamsolves.teamid = %s GROUP BY teamsolves.teamid, teamsolves.teamname, teamsolves.teamchannel, teamsolves.teamvoicechannel, teamsolves.teamhintcount;
        """


    def __init__(self, bot):
        self.bot = bot
        self._huntid = 'avatar'
        self._VARIABLES = {
            "Hide locked puzzles": True,
            "Non-meta same link": False,
            "Solving outside hunt duration": False
        }

        self._populate_text_strings()
    

    @commands.Cog.listener()
    async def on_ready(self):
        print('Cog "PuzzleHunt" Ready!')


    """
    STATIC METHODS
    """
    @staticmethod
    def sanitize_name(name):
        name = ''.join([c for c in name if c.isalnum() or c in '-_ ']).strip()
        name = name.replace(" ", "-").strip('-').strip('_')
        return name

    """
    BOT FUNCTIONS
    """
    def _get_hunt_info(self, huntid=None):
        if huntid is None and self._huntid is None:
            return None
        elif huntid is None:
            huntid = self._huntid
        cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunts WHERE huntid = %s", (huntid,))
        matching_hunt = cursor.fetchone()
        if matching_hunt:
            _, _, huntname, theme, starttime, endtime = matching_hunt
            # print(starttime)
            return {
                'ID': huntid,
                'Name': huntname,
                'Theme': theme,
                'Start time': starttime,
                'End time': endtime
            }
        else:
            return None

    def _populate_text_strings(self):
        for key_key, key_value in TextStringKey.__dict__.items():
            if not key_key.startswith('_'):
                self.TEXT_STRINGS[key_value] = key_value + ": UNDEFINED"

        # Default Strings For All Hunts
        text_cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_text_strings WHERE huntid = 'system'")
        text_strings = text_cursor.fetchall()
        for text_string in text_strings:
            _, _, key, value = text_string
            self.TEXT_STRINGS[key] = value

    def _get_team_info_from_member(self, memberid):
        if memberid is None or self._huntid is None:
            return None

        cursor = self.bot.db_execute(
            "SELECT * FROM puzzledb.puzzlehunt_solvers WHERE huntid = %s AND id = %s",
            (self._huntid, memberid))

        matching_solver = cursor.fetchone()
        if matching_solver:
            _, _, teamid, _ = matching_solver
        else:
            return None
        return self._get_team_info(teamid)
        

    def _get_team_info_from_name(self, teamname):
        cursor = self.bot.db_execute(
            "SELECT id FROM puzzledb.puzzlehunt_teams WHERE huntid = %s AND teamname = %s",
            (self._huntid, teamname))

        try:
            teamid = cursor.fetchone()[0]
        except:
            return None

        return self._get_team_info(teamid)

    def _get_team_info(self, teamid):
        if teamid is None or self._huntid is None:
            return None
        cursor = self.bot.db_execute(
            PuzzleHunt.TEAM_INFO_SQL.format(self.DATABASE_SCHEMA),
            (self._huntid, teamid)
        )
        matching_team = cursor.fetchone()
        if matching_team:
            teamid, teamname, last_solve, total_points, teamchannel, teamvoicechannel, teamhintcount = matching_team

            return {
                'Team ID': teamid,
                'Team Name': teamname,
                'Channel ID': teamchannel,
                'VC ID': teamvoicechannel,
                'Points': total_points,
                'Latest Solve Time': last_solve,
                'Hint Count': teamhintcount
            }
        return None

    async def _add_to_team(self, ctx, memberid, teamid):
        self.bot.db_execute(
            "INSERT INTO puzzledb.puzzlehunt_solvers (id, huntid, teamid) VALUES (%s, %s, %s)", 
            (memberid, self._huntid, teamid))
        team_info = self._get_team_info(teamid)
        team_channel = ctx.guild.get_channel(team_info['Channel ID'])
        team_voice_channel = ctx.guild.get_channel(team_info['VC ID'])
        member = ctx.guild.get_member(memberid)
        # role = discord.utils.get(ctx.guild.roles, name=HUNT_ROLE)
        # await member.add_roles(role)
        if team_channel:
            await team_channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True,
                read_message_history=True)
        
        await self._send_as_embed(ctx, "Successfully added member @{} to team `{}`.".format(member.display_name, team_info['Team Name']), "You can now access the team channel at #{}.".format(team_channel))
        await team_channel.send("Welcome to team `{}`, <@{}>!".format(team_info['Team Name'], memberid))


    async def _create_team(self, ctx, solverid, teamname):
        channelname = self.sanitize_name(teamname)
        await self._send_as_embed(ctx, "Creating a new team...")
        channel = await ctx.guild.create_text_channel(channelname, category=discord.utils.get(ctx.guild.categories, name=HUNT_CATEGORY))
        await channel.edit(topic=teamname)
        vc = await ctx.guild.create_voice_channel(channelname, category=discord.utils.get(ctx.guild.categories, name=HUNT_CATEGORY))
        await channel.set_permissions(
            ctx.guild.default_role,
            view_channel=False,
            read_messages=False,
            send_messages=False,
            read_message_history=False,
        )
        await vc.set_permissions(
            ctx.guild.default_role,
            view_channel=False,
            connect=False
        )
        await channel.set_permissions(
            ctx.author, 
            view_channel=True,
            read_messages=True,
            send_messages=True,
            read_message_history=True)
        await vc.set_permissions(
            ctx.author,
            view_channel=True,
            connect=True,
            speak=True)
        cursor = self.bot.db_execute(
            "INSERT INTO puzzledb.puzzlehunt_teams (huntid, teamname, teamchannel, teamvoicechannel, hintcount) VALUES (%s, %s, %s, %s, 0) returning id", 
            (self._huntid, teamname, channel.id, vc.id))
        teamid = cursor.fetchone()[0]

        await self._send_as_embed(channel, self.TEXT_STRINGS[TextStringKey.START_HUNT_INTRO_HEADER], self.TEXT_STRINGS[TextStringKey.START_HUNT_INTRO_TEXT])

        await self._add_to_team(ctx, ctx.author.id, teamid)


    """
    MEMBER FUNCTIONS
    """
    @commands.group(name="hunt", invoke_without_command=True)
    async def hunt(self, ctx):
        await self._hunt_help(ctx)

    @hunt.command(name="status")
    async def hunt_status(self, ctx):
        embed = discord.Embed(colour=EMBED_COLOUR)
        if self._huntid is not None:
            embed.set_author(name="Currently Running Puzzle Hunt:")
            hunt_info = self._get_hunt_info(self._huntid)
            if hunt_info is not None:
                for var in ['Start time', 'End time']:
                    if not hunt_info[var]:
                        await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.MISSING_VARIABLE].format(var))
                        return
                remaining = (hunt_info['End time'] - datetime.now()).total_seconds()
                to_go = (hunt_info['Start time'] - datetime.now()).total_seconds()
                embed.add_field(
                    name="Name",
                    value=hunt_info['Name'],
                    inline=False
                )
                embed.add_field(
                    name="Theme",
                    value=hunt_info['Theme'],
                    inline=False
                )
                embed.add_field(
                    name="Starts in" if to_go > 0 else "Time remaining",
                    value=strfdelta(to_go) if to_go > 0 else strfdelta(remaining) if remaining > 0 else "N.A.",
                    inline=False
                )
                embed.add_field(
                    name="-" * 18,
                    value=f"Not sure what to do? Start with `{self.bot.BOT_PREFIX}hunt help`!",
                    inline=False
                )
                
        else:
            embed.set_author(name=self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
        await ctx.send(embed=embed)


    @hunt.command(name="help", aliases=["commands", "tutorial"])
    async def _hunt_help(self, ctx):
        """
        Get an explanation of how the hunt function of the bot works.
        """
        async with ctx.typing(): 
            embed = discord.Embed(colour=EMBED_COLOUR)
            if self._huntid is not None:
                embed.set_author(name="Puzzle Hunt Commands:")
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt join <team name>",
                    value="Join / create a team",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt recruit <@ user>",
                    value="Recruit someone into your team",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt leave",
                    value="Leave your current team (deletes team if you are the last member)",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt puzzles",
                    value="View available puzzles",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt solve <puzzle id> <your answer>",
                    value="Attempt to solve a puzzle",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt team",
                    value="View your team info",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt leaderboard",
                    value="See the overall leaderboard",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt help",
                    value="See this list of commands",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt status",
                    value="See the status of the current hunt",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt faq / errata",
                    value="View frequently asked questions, errata and clarifications.",
                    inline=True)
                embed.add_field(
                    name=f"{self.bot.BOT_PREFIX}hunt requesthint [your question]",
                    value=f"Request a hint. `{self.bot.BOT_PREFIX}hunt hints` to see your hint tokens.",
                    inline=True)
                embed.set_footer(text=f'Still have questions? Mention our "@{HUNT_HELP_ROLE}" role and we\'ll be over to assist!')
            else:
                embed.set_author(name=self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
        await ctx.send(embed=embed)
        
    
    async def _send_as_embed(self, ctx, title, description=None, colour=EMBED_COLOUR):
        embed = discord.Embed(colour=colour)
        if description:
            embed.add_field(
                name=title,
                value=description,
                inline=False
            )
        else:
            embed.set_author(name=title)
        await ctx.send(embed=embed)

    async def _admin_send_as_embed(self, ctx, title, description=None):
        await self._send_as_embed(ctx, title, description, colour=ADMIN_EMBED_COLOUR)

    @hunt.command(name='answer', aliases=['solve'])
    async def solve(self, ctx, puzid=None, *attempt):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        async with ctx.typing(): 
            hunt_info = self._get_hunt_info()
            
        if hunt_info['Start time'] > datetime.now() and not self._VARIABLES['Solving outside hunt duration']:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.HUNT_NOT_STARTED])
            return
        async with ctx.typing(): 
            team_info = self._get_team_info_from_member(ctx.author.id)
        if team_info is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NOT_IN_A_TEAM])
            return
        if ctx.message.channel != ctx.guild.get_channel(team_info['Channel ID']):
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.WRONG_CHANNEL])
            return

        if puzid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.PUZZLE_ID_NOT_AVAILABLE], self.TEXT_STRINGS[TextStringKey.ANSWER_CLARIFICATION])
            return
        if len(attempt) == 0:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.ANSWER_CLARIFICATION])
            return

        async with ctx.typing():
            cursor = self.bot.db_execute("SELECT puzzleid FROM puzzledb.puzzlehunt_solves WHERE huntid = %s and teamid = %s;", (self._huntid, team_info['Team ID']))
            solves = cursor.fetchall()
        solved = [solve[0] for solve in solves]
        if puzid in solved:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.ALREADY_SOLVED])
            return

        async with ctx.typing(): 
            cursor = self.bot.db_execute("SELECT solvetime FROM puzzledb.puzzlehunt_bad_attempts WHERE huntid = %s and teamid = %s and puzzleid = %s;", (self._huntid, team_info['Team ID'], puzid))
            solvetimes = cursor.fetchall()
        if solvetimes:
            solvetimes = [solvetime[0] for solvetime in solvetimes]
            last_solvetime = sorted(solvetimes)[-1]
            time_passed = int((datetime.now() - last_solvetime).total_seconds())
            if time_passed < DELAY_AFTER_FAILING:
                await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.ATTEMPTING_TOO_SOON].format(DELAY_AFTER_FAILING - time_passed))
                return
            
        async with ctx.typing(): 
            cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_puzzles where huntid = %s and puzzleid = %s;", (self._huntid, puzid))
            puzzle = cursor.fetchone()
            cursor = self.bot.db_execute("SELECT partialanswer, response FROM puzzledb.puzzlehunt_puzzle_partials where huntid = %s and puzzleid = %s;", (self._huntid, puzid))
            partials = cursor.fetchall()
        if not puzzle:
            async with ctx.typing():
                cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_puzzles where huntid = %s and UPPER(name) = UPPER(%s);", (self._huntid, puzid))
                puzzle = cursor.fetchone()
        if not puzzle:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.PUZZLE_ID_NOT_AVAILABLE], self.TEXT_STRINGS[TextStringKey.ANSWER_CLARIFICATION])
            return
        _, _, _, name, description, relatedlink, points, requiredpoints, answer, unlock_override = puzzle
        unlocked = team_info['Points'] >= requiredpoints or unlock_override

        if not unlocked:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.PUZZLE_ID_NOT_AVAILABLE], self.TEXT_STRINGS[TextStringKey.ANSWER_CLARIFICATION])
            return

        attempt = ''.join(attempt).lower().replace(' ', '')
        answer = answer.lower().replace(' ', '')
        partial_dict = {partialanswer.lower(): response for partialanswer, response in partials}

        if attempt == answer:
            # Correct solve
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.CORRECT_ANSWER].format(points))
            if puzid == 'META':
                await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.FINISH_HUNT_OUTRO_HEADER], self.TEXT_STRINGS[TextStringKey.FINISH_HUNT_OUTRO_TEXT])
            self.bot.db_execute("INSERT INTO puzzledb.puzzlehunt_solves (huntid, puzzleid, solvetime, teamid) VALUES (%s, %s, %s, %s);", (self._huntid, puzid, datetime.now(), team_info['Team ID']))
        elif attempt in partial_dict:
            # Found an Intermediate Answer / Cluephrase
            await self._send_as_embed(ctx, "Keep going!", partial_dict[attempt])
            self.bot.db_execute("INSERT INTO puzzledb.puzzlehunt_bad_attempts (huntid, puzzleid, solvetime, teamid, attempt) VALUES (%s, %s, %s, %s, %s);", (self._huntid, puzid, datetime.now(), team_info['Team ID'], attempt))
            return
        else:
            # Wrong
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.WRONG_ANSWER])
            if len(attempt) <= 50:
                self.bot.db_execute("INSERT INTO puzzledb.puzzlehunt_bad_attempts (huntid, puzzleid, solvetime, teamid, attempt) VALUES (%s, %s, %s, %s, %s);", (self._huntid, puzid, datetime.now(), team_info['Team ID'], attempt))

    @hunt.command(name='join')
    async def join(self, ctx, *, teamname=""):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        if len(teamname) == 0:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.REGISTER_CLARIFICATION])
            return
        if self._get_team_info_from_member(ctx.author.id) is not None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.ALREADY_IN_A_TEAM])
            return
        
        if len(teamname) > 30:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.TEAM_NAME_LENGTH])
            return
        if len(self.sanitize_name(teamname)) == 0:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.TEAM_NAME_FORMAT])
            return
        # if "'" in teamname or '"' in teamname:
        #     await self._send_as_embed(ctx, "Illegal character(s) in your team name!")
        #     return
        cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_teams where huntid = %s and teamname = %s", (self._huntid, teamname))
        team = cursor.fetchone()
        if team is not None:
            teamid = team[0]
            cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_team_applications where huntid = %s and teamid = %s and solverid = %s", (self._huntid, teamid, ctx.author.id))
            app = cursor.fetchone()
            if app is not None:
                _, _, _, _, recruited, joined = app
                if recruited:
                    await self._add_to_team(ctx, ctx.author.id, teamid)
                else:
                    await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.TEAM_EXISTS])
            else:
                await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.TEAM_EXISTS])
                self.bot.db_execute("INSERT INTO puzzledb.puzzlehunt_team_applications (huntid, teamid, solverid, recruited, joined) VALUES (%s, %s, %s, FALSE, TRUE)", (self._huntid, teamid, ctx.author.id))
        else:
            await self._create_team(ctx, ctx.author.id, teamname)

    @hunt.command(name='recruit', aliases=['invite'])
    async def recruit(self, ctx, *mentions):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        
        if len(ctx.message.mentions) != 1:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.RECRUIT_CLARIFICATION])
            return

        team_info = self._get_team_info_from_member(ctx.author.id)
        if team_info is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NOT_IN_A_TEAM])
            return
        teamid = team_info['Team ID']

        recruitedid = ctx.message.mentions[0].id
        existed_in_team = self._get_team_info_from_member(recruitedid)
        if existed_in_team is not None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.RECRUITEE_IN_TEAM])

        cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_team_applications where huntid = %s and teamid = %s and solverid = %s", (self._huntid, teamid, recruitedid))
        app = cursor.fetchone()
        if app:
            _, _, _, _, recruited, joined = app
            if joined:
                await self._add_to_team(ctx, recruitedid, teamid)
            else:
                await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.WAITING_FOR_RECRUITEE])
        else:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.WAITING_FOR_RECRUITEE])
            self.bot.db_execute("INSERT INTO puzzledb.puzzlehunt_team_applications (huntid, teamid, solverid, recruited, joined) VALUES (%s, %s, %s, TRUE, FALSE)", (self._huntid, teamid, recruitedid))


    @hunt.command(name='leave')
    async def leave(self, ctx):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        async with ctx.typing(): 
            team_info = self._get_team_info_from_member(ctx.author.id)
        if team_info is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NOT_IN_A_TEAM])
            return
        teamid = team_info['Team ID']
        async with ctx.typing(): 
            cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_solvers WHERE huntid = %s AND teamid = %s", (self._huntid, teamid))
            members = cursor.fetchall()
            
            self.bot.db_execute("DELETE FROM puzzledb.puzzlehunt_solvers WHERE huntid = %s AND teamid = %s AND id = %s", (self._huntid, teamid, ctx.author.id))
        
        channel = ctx.guild.get_channel(team_info['Channel ID'])
        await channel.set_permissions(
            target=ctx.author, view_channel=False, read_messages=False, send_messages=False, read_message_history=False)
        voice_channel = ctx.guild.get_channel(team_info['VC ID'])
        await voice_channel.set_permissions(
            target=ctx.author, view_channel=False, connect=False, speak=False)

        if len(members) == 1:
            await self._send_as_embed(ctx, "You are the last member. The team will be deleted.")
            await channel.delete()
            await voice_channel.delete()
            self.bot.db_execute("DELETE FROM puzzledb.puzzlehunt_teams WHERE huntid = %s AND id = %s", (self._huntid, teamid))
    
    @hunt.command(name="leaderboard", aliases=["teams"])
    async def leaderboard(self, ctx):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return

        async with ctx.typing(): 
            hunt_info = self._get_hunt_info()
            embed = discord.Embed(colour=EMBED_COLOUR)
            embed.set_author(name=hunt_info['Name'] + " Leaderboard")

            cursor = self.bot.db_execute(
                self.LEADERBOARD_SQL,
                (self._huntid,))
            teams = cursor.fetchall()

        names = [str(i+1) + '. ' + team[0] for i, team in enumerate(teams)]
        if len(names) > 0 and teams[0][1]: names[0] = '🥇**' + names[0][2:] + '**'
        if len(names) > 1 and teams[1][1]: names[1] = '🥈**' + names[1][2:] + '**'
        if len(names) > 2 and teams[2][1]: names[2] = '🥉**' + names[2][2:] + '**'
        names = '\n'.join(names)
        points = '\n'.join([str(team[1]) for team in teams])
        times = '\n'.join(["--" if type(team[2]) == int or team[2] is None else datetime.strftime(team[2], "%d/%m %H:%M") for team in teams])

        if names == '':
            names = points = times = "--------"

        embed.add_field(name='Team', value=names, inline=True)
        embed.add_field(name='Points', value=points, inline=True)
        embed.add_field(name='Last solve', value=times, inline=True)

        await ctx.send(embed=embed)

    @hunt.command(name="faq", aliases=['errata'])
    async def view_faq(self, ctx):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        
        async with ctx.typing():
            cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_faq WHERE huntid = %s;", (self._huntid,))
            faqs = cursor.fetchall()
            cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_errata WHERE huntid = %s;", (self._huntid,))
            errata = cursor.fetchall()
            
        formatted_questions = []
        formatted_errata = []

        for faq in faqs:
            _, _, question, answer = faq
            formatted_questions += bold(question) + ' ' + answer,
        for erratum in errata:
            _, _, puzid, content = erratum
            if puzid is None or puzid in ["", "global", "general", "system"]:
                header = ""
            else:
                header = bold("(" + puz_id + ") ")
            formatted_errata += header + content,
        
        embed = discord.Embed(colour=EMBED_COLOUR)
        
        embed.add_field(name='FAQ', value='\n'.join(formatted_questions) if formatted_questions else 'No FAQ available.', inline=False)
        embed.add_field(name='Errata', value='\n'.join(formatted_errata) if formatted_errata else 'No errata has been given.', inline=False)
        await ctx.send(embed=embed)


    @hunt.command(name="team", aliases=['myteam', 'viewteam', 'teaminfo'])
    async def view_team(self, ctx):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        async with ctx.typing():
            team_info = self._get_team_info_from_member(ctx.author.id)
            if team_info is None:
                await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NOT_IN_A_TEAM])
                return

            cursor = self.bot.db_execute(
                "SELECT * FROM puzzledb.puzzlehunt_solvers WHERE huntid = %s and teamid = %s",
                (self._huntid, team_info['Team ID'])
            )
            
            members = cursor.fetchall()
        members = [ctx.guild.get_member(mem[1]).display_name for mem in members]

        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.set_author(name="Your Team:")
        
        embed.add_field(name='Name', value=team_info['Team Name'], inline=False)
        embed.add_field(name='Total points', value=team_info['Points'], inline=False)
        embed.add_field(name='Members', value='\n'.join(members), inline=False)
        await ctx.send(embed=embed)

        
    @hunt.command(name="puzzles")
    async def view_puzzles(self, ctx):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return

        async with ctx.typing():
            hunt_info = self._get_hunt_info()
        
        admin_role = discord.utils.get(ctx.guild.roles, name=HUNT_ADMIN_ROLE)

        if not hunt_info['Start time']:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.MISSING_VARIABLE].format('Start time'))

        if hunt_info['Start time'] > datetime.now() and not self._VARIABLES['Solving outside hunt duration'] and not admin_role in ctx.author.roles:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.HUNT_NOT_STARTED])
            return

        async with ctx.typing():
            team_info = self._get_team_info_from_member(ctx.author.id)
        if team_info is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NOT_IN_A_TEAM])
            return
        
        if ctx.message.channel != ctx.guild.get_channel(team_info['Channel ID']):
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.WRONG_CHANNEL])
            return

        async with ctx.typing():
            cursor = self.bot.db_execute("SELECT * FROM puzzledb.puzzlehunt_puzzles WHERE huntid = %s;", (self._huntid,))
            puzzles = cursor.fetchall()
            cursor = self.bot.db_execute("SELECT puzzleid FROM puzzledb.puzzlehunt_solves WHERE huntid = %s and teamid = %s;", (self._huntid, team_info['Team ID']))
            solves = cursor.fetchall()
            solves = [solve[0] for solve in solves]

        puzzleids = []
        names = []
        statuses = []
        answers = []

        puzzles = sorted(puzzles, key=lambda x: x[0])

        for puzzle in puzzles:
            _, _, puzzleid, name, description, relatedlink, points, requiredpoints, answer, unlock_override = puzzle
            solved = puzzleid in solves
            if team_info['Points'] >= requiredpoints or unlock_override:
                puzzleids.append(puzzleid)
                names.append("{}[{}]({}) ({} pts)".format("✅ " if solved else "⬛ ", name, relatedlink, points))
                statuses.append("SOLVED" if puzzleid in solves else "---")
                answers.append(answer.upper() if puzzleid in solves else "---")
            elif not self._VARIABLES['Hide locked puzzles']:
                # Puzzle locked, but can still be shown
                puzzleids.append('*' + puzzleid + '*')
                names.append("🔒 *{} ({} pts)*".format(name, points))
                statuses.append("*LOCKED*")
                answers.append('---')
        
        embed = discord.Embed(colour=EMBED_COLOUR)
        embed.set_author(name=hunt_info['Name'] + " Puzzles:")
        puzzleids = '\n'.join(puzzleids) if puzzleids else "----"
        names = '\n'.join(names) if names else "----"
        statuses = '\n'.join(statuses) if statuses else "----"
        answers = '\n'.join(answers) if answers else "-----"
        embed.add_field(name='ID', value=puzzleids, inline=True)
        embed.add_field(name='Puzzle', value=names, inline=True)
        # embed.add_field(name='Status', value=statuses, inline=True)
        embed.add_field(name='Answer', value=answers, inline=True)

        if self._VARIABLES['Non-meta same link']:
            embed.set_footer(text='All non-meta puzzles use the same link. You only need to open it once.')

        await ctx.send(embed=embed)

    @hunt.command(name='requesthint', aliases=['askforhint', 'hint', 'hints'])
    async def requesthint(self, ctx, *, hint_request_txt=""):
        if self._huntid is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return

        team_info = self._get_team_info_from_member(ctx.author.id)
        if team_info is None:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NOT_IN_A_TEAM])
            return
        hintcount = team_info['Hint Count']
        if hintcount is None:
            hintcount = 0
        minimum_hint_length = 30  # characters

        if ctx.message.channel != ctx.guild.get_channel(team_info['Channel ID']):
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.WRONG_CHANNEL])
            return

        if hint_request_txt == '':
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.HINT_INSTRUCTION].format(hintcount))
            return
        
        if len(hint_request_txt) < 30:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.HINT_INSTRUCTION].format(hintcount))
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.HINT_TOO_SHORT])
            return

        if hintcount <= 0:
            await self._send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HINTS_AVAILABLE])
            return

        hint_channel = discord.utils.get(ctx.guild.channels, name=HINT_CHANNEL)
        await self._admin_send_as_embed(hint_channel, f"Hint request from team `{team_info['Team Name']}`", hint_request_txt + f"\n\n[Jump To Message]({ctx.message.jump_url})")
        

    """
    ADMIN FUNCTIONS
    """
    @hunt.command(name="toggle")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def toggle_variable(self, ctx, *variable):
        if len(variable) == 0:
            await self._admin_send_as_embed(ctx, "Need to include variable to toggle.", "See the list below.")
            return
        variable = ' '.join(variable)
        if variable not in self._VARIABLES:
            await self._admin_send_as_embed(ctx, "Variable not found.", "See the list below.")
            return
        self._VARIABLES[variable] = not self._VARIABLES[variable]
        await self.view_variables(ctx)

    @hunt.command(name="variables")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def view_variables(self, ctx):
        variable_names = []
        variable_values = []
        for name, val in self._VARIABLES.items():
            variable_names += name,
            variable_values += 'TRUE' if val else 'FALSE',
        embed = discord.Embed(colour=ADMIN_EMBED_COLOUR)
        embed.set_author(name="Puzzle Hunt Variables:")
        embed.add_field(name='Variable', value="\n".join(variable_names), inline=True)
        embed.add_field(name='Value', value="\n".join(variable_values), inline=True)
        await ctx.send(embed=embed)

    @hunt.command(name="activate")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def activate(self, ctx, huntid=None):
        # Activate a hunt
        if huntid is not None:
            hunt_info = self._get_hunt_info(huntid)
            if hunt_info is None:
                await self._admin_send_as_embed(
                    ctx,
                    "Cannot activate hunt",
                    "`huntid` is not found. If this info is correct, please try again later!")
                return
        else:
            await self._admin_send_as_embed(
                ctx,
                "Activating a hunt",
                "To activate a hunt, include the correct `huntid` as parameter! To view hunt IDs, use `hunt settings`.")
            return
        self._huntid = huntid
        await self._send_as_embed(ctx, "Hunt activated.")
    
    @hunt.command(name="deactivate")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def deactivate(self, ctx):
        # Deactivate any running hunt
        if self._huntid is not None:
            await self._admin_send_as_embed(ctx, "Deactivated running hunt (`{}`).".format(self._huntid,))
            self._huntid = None
        else:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
    
    @hunt.command(name="purgeteam")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def purge_team(self, ctx, *, teamname):
        if self._huntid is None:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        if len(teamname) == 0:
            await self._admin_send_as_embed(ctx, "Need to provide team name!")
            return
        # teamname = ' '.join(teamname)
        async with ctx.typing(): 
            team_info = self._get_team_info_from_name(teamname)
        if team_info is None:
            await self._admin_send_as_embed(ctx, "No such team!")
            return
        try:
            await ctx.guild.get_channel(team_info['Channel ID']).delete()
            await ctx.guild.get_channel(team_info['VC ID']).delete()
        except:
            pass

        async with ctx.typing():
            self.bot.db_execute("DELETE FROM puzzledb.puzzlehunt_team_applications WHERE huntid = %s AND teamid = %s", (self._huntid, team_info['Team ID']))
            self.bot.db_execute("DELETE FROM puzzledb.puzzlehunt_solvers WHERE huntid = %s AND teamid = %s", (self._huntid, team_info['Team ID']))
            self.bot.db_execute("DELETE FROM puzzledb.puzzlehunt_solves WHERE huntid = %s AND teamid = %s", (self._huntid, team_info['Team ID']))
            self.bot.db_execute("DELETE FROM puzzledb.puzzlehunt_teams WHERE huntid = %s AND id = %s", (self._huntid, team_info['Team ID']))
        await self._admin_send_as_embed(ctx, "Team has been deleted.")

    @hunt.command(name="granthint", aliases=["granthints", "givehint", "givehints"])
    @has_any_role(HUNT_ADMIN_ROLE)
    async def grant_hint(self, ctx, *, args=""):
        if self._huntid is None:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return

        number = args.split(' ')[-1]
        try:
            hint_increment = int(number)
        except ValueError:
            await self._admin_send_as_embed(ctx, "You done fucked up son", "Make sure it's in the format: `hunt givehint [teamname] [number]")
            return

        team_name = ' '.join(args.split(' ')[:-1])
        team_info = self._get_team_info_from_name(team_name)
        if team_info is None:
            await self._admin_send_as_embed(ctx, f"No team named `{team_name}`!")
            return
        
        hintcount = team_info['Hint Count']
        if hintcount is None:
            hintcount = 0

        self.bot.db_execute(
            """UPDATE puzzledb.puzzlehunt_teams SET hintcount =
                (CASE
                    WHEN hintcount IS NULL THEN %s
                    ELSE hintcount + %s
                END) WHERE huntid = %s AND id = %s""", 
            (hint_increment, hint_increment, self._huntid, team_info['Team ID']))
        
        await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.YOU_GAVE_HINTS].format(hint_increment, team_name))


    @hunt.command(name="grantglobalhint", aliases=["giveglobalhint", "givehintglobal"])
    @has_any_role(HUNT_ADMIN_ROLE)
    async def grant_hint_globally(self, ctx, *, args=""):
        if self._huntid is None:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        
        if args.strip() == '':
            hint_increment = 1
        else:
            try:
                hint_increment = int(args.strip())
            except ValueError:
                await self._admin_send_as_embed(ctx, "You done fucked up son", "Make sure it's in the format: `hunt giveglobalhint [number]")
                return
    
        self.bot.db_execute(
            """UPDATE puzzledb.puzzlehunt_teams SET hintcount = 
                ( CASE 
                    WHEN hintcount IS NULL THEN %s
                    ELSE hintcount + %s
                END ) WHERE huntid = %s""", (hint_increment, hint_increment, self._huntid,))
        
        await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.YOU_GAVE_HINTS].format(hint_increment, "EVERYONE"))


    @hunt.command(name="admin")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def admin_help(self, ctx):
        async with ctx.typing(): 
            embed = discord.Embed(colour=ADMIN_EMBED_COLOUR)
            embed.set_author(name="Puzzle Hunt Admin Interface:")
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt activate [hunt ID]",
                value="Activate a hunt (this will be the currently running hunt)",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt deactivate",
                value="Deactivate the currently running hunt",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt purgeteam [team name]",
                value="Delete a team and all its member info",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt variables",
                value="View hunt related variables",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt toggle [variable text]",
                value="Change a variable from TRUE to FALSE (and vice versa)",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt unlockall",
                value="Unlock all puzzles (for the end of hunt).",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt givehint [team name] [N]",
                value="Give N hint tokens to a team",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt giveglobalhint [N]",
                value="Give N hint tokens to ALL hunting teams",
                inline=True)
            embed.add_field(
                name=f"{self.bot.BOT_PREFIX}hunt announce [announcement]",
                value="Make an announcement to all hunting teams",
                inline=True)
            embed.set_footer(text=f'Still have questions? Mention our "{HUNT_HELP_ROLE}" role and we\'ll be over to assist!')

            await ctx.send(embed=embed)

    @hunt.command(name="unlockall")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def unlock_all_puzzles(self, ctx):
        if self._huntid is None:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        
        self.bot.db_execute("UPDATE puzzledb.puzzlehunt_puzzles SET unlockoverride = TRUE WHERE huntid = %s", (self._huntid,))

        await self._admin_send_as_embed(ctx, "You just unlocked every puzzle globally.", "`hunt undounlock` to undo this!")

    @hunt.command(name="undounlock")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def undo_unlock_all(self, ctx):
        if self._huntid is None:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        
        self.bot.db_execute("UPDATE puzzledb.puzzlehunt_puzzles SET unlockoverride = FALSE WHERE huntid = %s", (self._huntid,))

        await self._admin_send_as_embed(ctx, "You've reset all puzzles back to their original status.")

    @hunt.command(name="announce")
    @has_any_role(HUNT_ADMIN_ROLE)
    async def announce(self, ctx, *, announcement_txt):
        # Announce to all hunting teams
        if self._huntid is None:
            await self._admin_send_as_embed(ctx, self.TEXT_STRINGS[TextStringKey.NO_HUNT_RUNNING])
            return
        
        cursor = self.bot.db_execute("SELECT teamchannel FROM puzzledb.puzzlehunt_teams WHERE huntid = %s", (self._huntid,))
        team_channels = cursor.fetchall()

        for channel_id in team_channels:
            team_channel = ctx.guild.get_channel(channel_id[0])
            if team_channel:
                await self._admin_send_as_embed(team_channel, "ANNOUNCEMENT", announcement_txt)

        hunt_main = discord.utils.get(ctx.guild.channels, name=HUNT_MAIN_CHANNEL)
        await self._admin_send_as_embed(hunt_main, "ANNOUNCEMENT", announcement_txt)


def setup(bot):
    bot.add_cog(PuzzleHunt(bot))
