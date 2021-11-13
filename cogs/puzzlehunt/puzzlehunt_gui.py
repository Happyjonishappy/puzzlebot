# puzzlehunt_gui.py
import os
import re
import psycopg2
import PySimpleGUI as sg
from json import load, dump
from datetime import datetime

POSTGRESQL_SERVER = "postgresql://theducvu@localhost:5432/theducvu"
re_match = re.compile(r".*@([A-z0-9]*:[0-9]*\/[A-z0-9]*)").match(POSTGRESQL_SERVER)
server_shorthand = re_match.groups()[0] if re_match else POSTGRESQL_SERVER

curdir = lambda p: os.path.join(os.path.abspath(os.path.dirname(__file__)), p)

ICON = b'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'
DARK_THEME = "DarkGrey2"
LIGHT_THEME = "LightGrey1"

config_file = "config.json"
config_file = curdir(config_file)

def loadconfig():
    with open(config_file, "r") as f:
        return load(f)

def dumpconfig(obj):
    with open(config_file, "w") as f:
        dump(obj, f)

config = loadconfig()
is_dark_theme = config["darktheme"]

sg.theme(DARK_THEME if is_dark_theme else LIGHT_THEME)


class PuzzlehuntGUI(object):
    WINDOW_TITLE = "Puzzlebot Database GUI"
    MAIN_FRAME_TITLE = "Database Admin Interface"

    IS_DARK_THEME = is_dark_theme

    TABS = [
        "-HUNTINFO_TAB-",
        "-PUZZLES_TAB-",
        "-TEAMS_TAB-",
        "-FAQ_ERRATA_TAB-",
        "-INFOSTRINGS_TAB-"
    ]

    TABLES = [
        '-PUZZLES_TABLE-',
        '-PARTIALS_TABLE-',
        '-TEAMS_TABLE-',
        '-FAQ_TABLE-',
        '-ERRATA_TABLE-',
        '-INFOSTRINGS_TABLE-'
    ]

    OTHER_TABLES = [
        '-TEAM_SOLVES_TABLE-',
        '-TEAM_ATTEMPTS_TABLE-',
        '-TEAM_MEMBERS_TABLE-',
        '-INFOSTRINGS_TABLE-'
    ]

    DEFAULT_HUNT_INFOSTRINGS = ['Start Hunt Intro Header', 'Start Hunt Intro Text', 'Finish Hunt Outro Header', 'Finish Hunt Outro Text']

    def __init__(self):
        self.selected_tab = None
        self._selected = {
            "Puzzle": None,
            "Partial": None,
            "Team": None,
            "FAQ": None,
            "Erratum": None,
            "Info String": None
        }
        self._huntid = None

        self._make_window()
        self._setup_database()

    def _make_window(self):
        HUNT_MENU_FRAME = sg.Frame(
            "Hunts",
            [
                [
                    sg.Table(
                        values=[], headings=['Hunt ID'],
                        col_widths=[20],
                        auto_size_columns=False,
                        justification='left',
                        enable_events=True,
                        num_rows=20, key='-HUNTIDTABLE-'),
                ],
                [
                    sg.Column(
                        [[sg.Button("Add", key="-ADDHUNT_BTN-"),
                        sg.Button("Delete", key="-DELHUNT_BTN-")]]
                    )
                ],
            ]
        )

        tab1_layout = [
            [
                sg.Column(
                [[
                    sg.Column([
                        [sg.Text("ID:")],
                        [sg.Text("Name:")],
                        [sg.Text("Theme:")],
                        [sg.Text("Start Time:")],
                        [sg.Text("End Time:")],
                    ]),
                    sg.Column([
                        [sg.Input(key="-HUNTINFO_ID_INP-")],
                        [sg.Input(key="-HUNTINFO_NAME_INP-")],
                        [sg.Input(key="-HUNTINFO_THEME_INP-")],
                        [sg.Input(key="-HUNTINFO_STARTTIME_INP-")],
                        [sg.Input(key="-HUNTINFO_ENDTIME_INP-")]
                    ])
                ]])
            ],
            [sg.Button("Update", key="-UPDATEHUNTINFO-")]
        ]

        tab2_layout = [
            [sg.Table(
                values=[['--'] * 7], headings=["ID", "Name", "Description", "Link", "Points", "Points to Unlock", "Answer"],
                max_col_width=1200,
                col_widths=[20] * 7,
                auto_size_columns=False,
                alternating_row_color=self.get_alt_row_colour(),
                justification='left',
                enable_events=True,
                num_rows=12, key='-PUZZLES_TABLE-')
            ],
            [sg.Column([[
                sg.Column(
                    [
                        [
                            sg.Button("Add", key="-ADDPUZ_BTN-"), 
                            sg.Button("Delete", key="-DELPUZ_BTN-"),
                        ],
                        [
                            sg.Column(
                                [[
                                    sg.Column([
                                        [sg.Text("ID:")],
                                        [sg.Text("Name:")],
                                        [sg.Text("Description:")],
                                        [sg.Text("Link:")],
                                        [sg.Text("Points:")],
                                        [sg.Text("Required Points:")],
                                        [sg.Text("ANSWER:")],
                                    ]),
                                    sg.Column([
                                        [sg.Input(key="-PUZZLE_ID_INP-")],
                                        [sg.Input(key="-PUZZLE_NAME_INP-")],
                                        [sg.Input(key="-PUZZLE_DESC_INP-")],
                                        [sg.Input(key="-PUZZLE_LINK_INP-")],
                                        [sg.Input(key="-PUZZLE_POINTS_INP-")],
                                        [sg.Input(key="-PUZZLE_REQPOINTS_INP-")],
                                        [sg.Input(key="-PUZZLE_ANSWER_INP-", text_color="grey")]
                                    ])
                                ]]
                            )
                        ],
                        [
                            sg.Button("Update", key="-UPDATE_PUZ-")
                        ]
                    ],
                ),
                sg.Column(
                    [
                        [sg.Text("Intermediate / Partial Answers (Cluephrases)")],
                        [sg.Table(
                            values=[['--'] * 3], headings=["Puzzle", "Trigger", "Response"],
                            max_col_width=120,
                            col_widths=[20] * 3,
                            auto_size_columns=True,
                            alternating_row_color=self.get_alt_row_colour(),
                            justification='left',
                            enable_events=True,
                            num_rows=6, key='-PARTIALS_TABLE-')
                        ],
                        [
                            sg.Button("Add", key="-ADDPARTIAL_BTN-"), 
                            sg.Button("Delete", key="-DELPARTIAL_BTN-"),
                        ],
                        [
                            sg.Column(
                            [[
                                sg.Column([
                                    [sg.Text("Puzzle ID:")],
                                    [sg.Text("Trigger:")],
                                    [sg.Text("Response:")],
                                ]),
                                sg.Column([
                                    [sg.Input(key="-PARTIAL_PUZZLE_INP-", disabled=True)],
                                    [sg.Input(key="-PARTIAL_TRIGGER_INP-")],
                                    [sg.Input(key="-PARTIAL_RESPONSE_INP-")],
                                ])
                            ]]),
                            sg.Button("Update", key="-UPDATE_PARTIAL-")
                        ]
                ])
            ]])]
        ]

        tab3_layout = [
            [
                sg.Column([[
                    sg.Frame(
                        "Teams",
                        [[
                            sg.Table(
                                values=[['--'] * 5], headings=["ID", "Name", "Last solve", "Points", "Hint Tokens"],
                                max_col_width=1200,
                                col_widths=[20] * 5,
                                auto_size_columns=True,
                                alternating_row_color=self.get_alt_row_colour(),
                                justification='left',
                                enable_events=True,
                                num_rows=12, key='-TEAMS_TABLE-'
                            )
                        ]],
                        key='-TEAMS_FRAME-'
                    ),
                    sg.Frame(
                        "Members",
                        [[
                            sg.Table(
                                values=[['--'] * 1], headings=["Discord ID"],
                                max_col_width=1200,
                                col_widths=[20] * 1,
                                auto_size_columns=True,
                                alternating_row_color=self.get_alt_row_colour(),
                                justification='left',
                                enable_events=True,
                                num_rows=12, key='-TEAM_MEMBERS_TABLE-'
                            )
                        ]],
                        key='-TEAM_MEMBERS_FRAME-'
                    )
                ]], key='-TEAMS_ROW1-'),
            ],
            [
                sg.Column(
                [[
                    sg.Column([
                        [sg.Text("Team ID:")],
                        [sg.Text("Team Name:")],
                        [sg.Text("Hint Tokens:")],
                    ]),
                    sg.Column([
                        [sg.Input(key="-TEAM_ID_INP-")],
                        [sg.Input(key="-TEAM_NAME_INP-")],
                        [sg.Input(key="-TEAM_HINTS_INP-")],
                    ])
                ]]),
                sg.Button("Update", key="-UPDATE_TEAM-")
            ],
            [
                sg.Column([[
                    sg.Frame(
                        "Solves",
                        [[
                            sg.Table(
                                values=[['--'] * 2], headings=["Puzzle ID", "Solve time"],
                                max_col_width=120,
                                col_widths=[20] * 2,
                                auto_size_columns=True,
                                alternating_row_color=self.get_alt_row_colour(),
                                justification='left',
                                enable_events=True,
                                num_rows=12, key='-TEAM_SOLVES_TABLE-'
                            )
                        ]],
                        key='-TEAM_SOLVES_FRAME-'
                    ),
                    sg.Frame(
                        "Attempts",
                        [[
                            sg.Table(
                                values=[['--'] * 3], headings=["Puzzle ID", "Attempt", "Time"],
                                max_col_width=120,
                                col_widths=[20] * 3,
                                auto_size_columns=True,
                                alternating_row_color=self.get_alt_row_colour(),
                                justification='left',
                                enable_events=True,
                                num_rows=12, key='-TEAM_ATTEMPTS_TABLE-'
                            )
                        ]],
                        key='-TEAM_ATTEMPTS_FRAME-'
                    )
                ]], key='-TEAMS_ROW2-'),
            ]
        ]

        tab4_layout = [[
            sg.Frame("FAQ", [
                [
                    sg.Table(
                        values=[['--'] * 3], headings=["ID", "Question", "Answer"],
                        max_col_width=120,
                        col_widths=[20] * 3,
                        auto_size_columns=True,
                        alternating_row_color=self.get_alt_row_colour(),
                        justification='left',
                        enable_events=True,
                        num_rows=12, key='-FAQ_TABLE-')
                ],
                [
                    sg.Column(
                    [[
                        sg.Button("Add", key="-ADDFAQ_BTN-"), 
                        sg.Button("Delete", key="-DELFAQ_BTN-")
                    ]]),
                ],
                [
                    sg.Column(
                    [[
                        sg.Column([
                            [sg.Text("ID:")],
                            [sg.Text("Question:")],
                            [sg.Text("Answer:")],
                        ]),
                        sg.Column([
                            [sg.Input(key="-FAQ_ID_INP-")],
                            [sg.Input(key="-FAQ_QSN_INP-")],
                            [sg.Input(key="-FAQ_ANS_INP-")],
                        ])
                    ]]),
                    sg.Button("Update", key="-UPDATE_FAQ-")
                ]
            ]),
            sg.Frame("Errata", [
                [
                    sg.Table(
                        values=[['--'] * 3], headings=["ID", "Puzzle ID", "Erratum"],
                        max_col_width=120,
                        col_widths=[20] * 3,
                        auto_size_columns=True,
                        alternating_row_color=self.get_alt_row_colour(),
                        justification='left',
                        enable_events=True,
                        num_rows=12, key='-ERRATA_TABLE-')
                ],
                [
                    sg.Column(
                    [[
                        sg.Button("Add", key="-ADDERR_BTN-"), 
                        sg.Button("Delete", key="-DELERR_BTN-")
                    ]]),
                ],
                [
                    sg.Column(
                    [[
                        sg.Column([
                            [sg.Text("ID:")],
                            [sg.Text("Puzzle ID:")],
                            [sg.Text("Erratum Text:")],
                        ]),
                        sg.Column([
                            [sg.Input(key="-ERR_ID_INP-")],
                            [sg.Input(key="-ERR_PUZ_INP-")],
                            [sg.Input(key="-ERR_TEXT_INP-")],
                        ])
                    ]]),
                    sg.Button("Update", key="-UPDATE_ERR-")
                ]
            ])
        ]]

        tab5_layout = [
            [sg.Table(
                values=[['--'] * 3], headings=["Hunt Specific?", "Key", "Text"],
                max_col_width=120,
                col_widths=[100, 500, 800],
                auto_size_columns=True,
                alternating_row_color=self.get_alt_row_colour(),
                justification='left',
                enable_events=True,
                num_rows=12, key='-INFOSTRINGS_TABLE-')],
            [
                sg.Column(
                [[
                    sg.Column([
                        [sg.Text("Domain:")],
                        [sg.Text("Key:")],
                        [sg.Text("Text:")],
                    ]),
                    sg.Column([
                        [sg.Input(key="-INFO_DOMAIN_INP-", disabled=True)],
                        [sg.Input(key="-INFO_KEY_INP-", disabled=True)],
                        [sg.Input(key="-INFO_TEXT_INP-")],
                    ])
                ]]),
                sg.Button("Update", key="-UPDATE_INFOSTRING-")
            ]
        ]

        DATA_FRAME = sg.Frame(
            "Hunt: ",
            [
                [
                    sg.TabGroup([[
                        sg.Tab("Hunt Info", tab1_layout, key="-HUNTINFO_TAB-"),
                        sg.Tab("Puzzles", tab2_layout, key="-PUZZLES_TAB-"),
                        sg.Tab("Teams", tab3_layout, key="-TEAMS_TAB-"),
                        sg.Tab("FAQ / Errata", tab4_layout, key="-FAQ_ERRATA_TAB-"),
                        sg.Tab("Info Strings", tab5_layout, key="-INFOSTRINGS_TAB-"),
                    ]], key="-TABGROUP-", enable_events=True)
                ]
            ],
            key='-DATAFRAME-'
        )

        MAIN_FRAME_LAYOUT = [
            [ 
                sg.Button("Save Layout", key="-SAVE_LAYOUT-"),
                sg.Button("Toggle Light / Dark Theme...", key="-DARKTHEMETOGGLE-"),
                sg.Text(f"Connected to {server_shorthand}")
            ],
            [
                sg.Frame(
                    self.MAIN_FRAME_TITLE,
                    [[
                        sg.Column([[
                            sg.Column([
                                [HUNT_MENU_FRAME],
                                [sg.Button("Direct Query", button_color="red", key="-DIRECT_QUERY-")]
                            ]), DATA_FRAME
                        ]], key="-INNER_MAINFRAME-"),
                    ]],
                    key='-MAINFRAME-'
                )
            ]
        ]
        
        self.window = sg.Window(
            self.WINDOW_TITLE, MAIN_FRAME_LAYOUT, 
            resizable=True, finalize=True,
            icon=ICON
        )
        
        self.window['-MAINFRAME-'].expand(True, True)
        self.window['-TABGROUP-'].expand(True, True)
        self.window['-INNER_MAINFRAME-'].expand(True, True)
        # HUNT_MENU_FRAME.expand(expand_x=1, expand_y=True)
        DATA_FRAME.expand(10, True)
        self.window['-PUZZLES_TABLE-'].expand(True, True)
        self.window['-PARTIALS_TABLE-'].expand(True, True)
        self.window['-TEAMS_TABLE-'].expand(True, True)
        self.window['-FAQ_TABLE-'].expand(True, True)
        self.window['-ERRATA_TABLE-'].expand(True, True)
        self.window['-INFOSTRINGS_TABLE-'].expand(True, True)
        self.window['-TEAMS_FRAME-'].expand(True, True)
        self.window['-TEAM_MEMBERS_FRAME-'].expand(True, True)
        self.window['-TEAM_SOLVES_FRAME-'].expand(True, True)
        self.window['-TEAM_ATTEMPTS_FRAME-'].expand(True, True)
        self.window['-TEAMS_TABLE-'].expand(True, True)
        self.window['-TEAM_MEMBERS_TABLE-'].expand(True, True)
        self.window['-TEAM_SOLVES_TABLE-'].expand(True, True)
        self.window['-TEAM_ATTEMPTS_TABLE-'].expand(True, True)
        self.window['-TEAMS_ROW1-'].expand(True, True)
        self.window['-TEAMS_ROW2-'].expand(True, True)

        self.window.bind("<Escape>", "-ESCAPE-")
        self.window.bind("<q>", "-ESCAPE-")
        self.window.set_min_size((800, 600))
        self._load_layout()
    
    def get_alt_row_colour(self):
        return "#1f1c19" if self.IS_DARK_THEME else "#ebf5fa"

    def _setup_database(self):
        self.sql_db = psycopg2.connect(POSTGRESQL_SERVER, sslmode="allow")
        self.sql_db.autocommit = True

        self._data = {
            "Hunts": [],
            "Hunt Info": [],
            "Puzzles": [],
            "Teams": [],
            "FAQ / Errata": [],
            "Info Strings": []
        }

        self._populate_initial_data()

    def _update_theme(self):
        sg.theme(DARK_THEME if self.IS_DARK_THEME else LIGHT_THEME)
        self.window.close()
        self._make_window()
        self.refresh_hunt_table()
    
    def _load_layout(self):
        if 'size' in config:
            size = config["size"]
            self.window.size = size

        if 'tables' in config:
            for table, widths in config['tables'].items():
                table_widget = self.window[table].Widget
                for i, width in enumerate(widths):
                    table_widget.column(i, width=width)
                table_widget.pack(side="left", fill="both", expand=True)

    def _save_layout(self):
        config['size'] = self.window.size

        tables = {}
        for table in self.TABLES + self.OTHER_TABLES:
            tables[table] = [self.window[table].Widget.column(i)['width'] for i in range(len(self.window[table].ColumnHeadings))]
        config['tables'] = tables
        
        dumpconfig(config)

    def run(self):
        while True:
            event, values = self.window.read()

            if event == "-ESCAPE-":
                self._save_layout()
                if sg.popup_yes_no("Are you sure you want to exit?") == 'Yes':
                    break
            elif event == sg.WIN_CLOSED:
                break

            elif event == "-DARKTHEMETOGGLE-":
                answer = sg.popup_yes_no("This will restart the GUI. Continue?")
                if answer == "Yes":
                    self.IS_DARK_THEME = not self.IS_DARK_THEME
                    config['darktheme'] = self.IS_DARK_THEME
                    dumpconfig(config)
                    self._update_theme()
                    self._populate_initial_data()

            elif event == "-HUNTIDTABLE-":
                selected_hunt_idx = values[event][0]
                self._huntid = self._data["Hunts"][selected_hunt_idx]
                self.window['-DATAFRAME-'].update(value="Hunt: " + self._huntid)
                # print(f"Selected {self._huntid}")
                self._update_data_frame()
            
            elif event == "-TABGROUP-":
                self._select_tab(values[event])

            elif event == "-ADDHUNT_BTN-":
                self._add_new_hunt()
            elif event == "-DELHUNT_BTN-":
                self._delete_hunt()
            elif event == "-UPDATEHUNTINFO-":
                self._update_hunt_info(values)

            elif event == "-ADDPUZ_BTN-":
                self._add_puzzle()
            elif event == "-DELPUZ_BTN-":
                self._delete_puzzle()
            elif event == "-UPDATE_PUZ-":
                self._update_puzzle(values)          
            
            elif event == "-ADDPARTIAL_BTN-":
                self._add_partial()
            elif event == "-DELPARTIAL_BTN-":
                self._delete_partial()
            elif event == "-UPDATE_PARTIAL-":
                self._update_partial(values)

            elif event == "-ADDFAQ_BTN-":
                self._add_faq()
            elif event == "-DELFAQ_BTN-":
                self._delete_faq()
            elif event == "-UPDATE_FAQ-":
                self._update_faq(values)

            elif event == "-ADDERR_BTN-":
                self._add_erratum()
            elif event == "-DELERR_BTN-":
                self._delete_erratum()
            elif event == "-UPDATE_ERR-":
                self._update_erratum(values)

            elif event == "-UPDATE_INFOSTRING-":
                self._update_info_string(values)

            elif event == "-UPDATE_TEAM-":
                self._update_team(values)
            
            elif event == "-SAVE_LAYOUT-":
                self._save_layout()

            elif event == "-DIRECT_QUERY-":
                self._direct_query()

            elif event in self.TABLES:
                if values[event]:
                    # from IPython import embed; embed()
                    if event == "-PUZZLES_TABLE-":
                        if values[event][0] != self._selected["Puzzle"]:
                            self.populate_puzzles(selected=values[event][0])
                    elif event == "-PARTIALS_TABLE-":
                        if values[event][0] != self._selected["Partial"]:
                            self._selected["Partial"] = values[event][0]
                            self.populate_puzzles(selected=self._selected["Puzzle"], selected_partial=self._selected["Partial"])
                    elif event == "-TEAMS_TABLE-":
                        if values[event][0] != self._selected["Team"]:
                            self.populate_teams(selected=values[event][0])
                    elif event == "-FAQ_TABLE-":
                        if values[event][0] != self._selected["FAQ"]:
                            self.populate_faq(selected=values[event][0])
                    elif event == "-ERRATA_TABLE-":
                        if values[event][0] != self._selected["Erratum"]:
                            self.populate_errata(selected=values[event][0])
                    elif event == "-INFOSTRINGS_TABLE-":
                        if values[event][0] != self._selected["Info String"]:
                            self.populate_infostrings(selected=values[event][0])

        self.window.close()

    def _update_data_frame(self):
        if not self.selected_tab:
            self.selected_tab = "-HUNTINFO_TAB-"
        
        self._update_data_table()
    
    def _update_data_table(self):
        if self.selected_tab == "-HUNTINFO_TAB-":
            self.fill_huntinfo_input("","","","","")
            self.db_get_hunts()
            self.populate_huntinfo()
        elif self.selected_tab == "-PUZZLES_TAB-":
            self.fill_puzzle_input("","","","","","","")
            self.fill_partial_input("","","")
            self.db_get_puzzles()
            self.populate_puzzles()
        elif self.selected_tab == "-TEAMS_TAB-":
            self.fill_team_input("", "", "")
            self.db_get_teams()
            self.populate_teams()
        elif self.selected_tab == "-FAQ_ERRATA_TAB-":
            self.fill_errata_input("", "", "")
            self.db_get_faq()
            self.populate_faq()
            self.db_get_errata()
            self.populate_errata()
        elif self.selected_tab == "-INFOSTRINGS_TAB-":
            self.fill_infostring_input("", "", "")
            self.db_get_infostrings()
            self.populate_infostrings()
        else:
            raise ValueError(f"Unrecognised selected_tab: {self.selected_tab}")

    def _select_tab(self, selected_tab):
        self.selected_tab = selected_tab
        self._update_data_frame()

    def _populate_initial_data(self):
        if not self._data["Hunts"]:
            self.refresh_hunt_table()

            if not self._data["Hunts"]:
                self.window['-PUZZLES_TAB-'].update(disabled=True)
                self.window['-TEAMS_TAB-'].update(disabled=True)
                self.window['-FAQ_ERRATA_TAB-'].update(disabled=True)
                self.window['-INFOSTRINGS_TAB-'].update(disabled=True)
                return
        self.window['-PUZZLES_TAB-'].update(disabled=False)
        self.window['-TEAMS_TAB-'].update(disabled=False)
        self.window['-FAQ_ERRATA_TAB-'].update(disabled=False)
        self.window['-INFOSTRINGS_TAB-'].update(disabled=False)
        self._huntid = self._data["Hunts"][0]
        self.window['-DATAFRAME-'].update(value="Hunt: " + self._huntid)
        huntid, name, theme, start_t, end_t = self._data["Hunt Info"][0]

        self.fill_huntinfo_input(huntid, name, theme, start_t, end_t)

    def _add_new_hunt(self):
        newhuntid = sg.popup_get_text("Enter new hunt ID:")
        if newhuntid in self._data["Hunts"]:
            sg.popup_error("huntid already exists!")
            return
        
        if newhuntid == "" or newhuntid is None:
            sg.popup_error("Hunt ID is required!")
            return
        
        try:
            cursor = self.sql_db.cursor()
            cursor.execute("INSERT INTO puzzledb.puzzlehunts (huntid,huntname,theme,starttime,endtime) VALUES (%s,'Undefined','Undefined','01-01-1970 00:00:01.000000','01-01-1970 00:00:01.000000');", (newhuntid,))
            for key in self.DEFAULT_HUNT_INFOSTRINGS:
                cursor.execute("""INSERT INTO puzzledb.puzzlehunt_text_strings (huntid,textkey,textstring) VALUES (%s,%s,'Undefined');""", (newhuntid, key))
            # sg.popup("Successful!")
        except Exception as e:
            sg.popup_error("Failed to add hunt! Error:", e)
        self.refresh_hunt_table()

    def _delete_hunt(self):
        hunt = self._huntid
        if not hunt:
            sg.popup("No Hunt selected!")
            return

        ans = sg.popup_yes_no(f"Are you sure you want to delete this hunt: {hunt}?")
        if ans == 'Yes':
            try:
                cursor = self.sql_db.cursor()
                cursor.execute("DELETE FROM puzzledb.puzzlehunts WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_puzzles WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_teams WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_solvers WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_attempts WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_text_strings WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_puzzle_partials WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_faq WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_errata WHERE huntid = %s", (hunt,))
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_team_applications WHERE huntid = %s", (hunt,))
                # sg.popup("Successful!")
                self._huntid = None
                self.fill_huntinfo_input("","","","","")
                self._populate_initial_data()
                self.window['-TABGROUP-'].Widget.select(0)
            except Exception as e:
                sg.popup_error("Failed to delete hunt! Error:", e)
            self.refresh_hunt_table()

    def _update_hunt_info(self, values):
        if not self._huntid:
            return

        huntid = values["-HUNTINFO_ID_INP-"]
        name = values["-HUNTINFO_NAME_INP-"]
        theme = values["-HUNTINFO_THEME_INP-"]
        start_t = values["-HUNTINFO_STARTTIME_INP-"]
        end_t = values["-HUNTINFO_ENDTIME_INP-"]

        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunts SET huntid = %s, huntname = %s, theme = %s, starttime = %s, endtime = %s WHERE huntid = %s", 
            (huntid, name, theme, start_t, end_t, self._huntid,))
            self.refresh_hunt_table()
            sg.popup(f"Successfully updated hunt {huntid}!")
        except Exception as e:
            sg.popup("Failed to update hunt. Error:", e)

    def _add_puzzle(self):
        new_puz_id = sg.popup_get_text("Enter new puzzle ID:")
        if new_puz_id in [puz[0] for puz in self._data["Puzzles"]]:
            sg.popup_error("Puzzle ID already exists!")
            return
        
        if new_puz_id == "" or new_puz_id is None:
            sg.popup_error("Puzzle ID is required!")
            return
        
        try:
            cursor = self.sql_db.cursor()
            cursor.execute("""INSERT INTO puzzledb.puzzlehunt_puzzles 
                    (huntid,puzzleid,name,description,relatedlink,points,requiredpoints,answer) 
                    VALUES (%s,%s,'Undefined','Undefined','http://undefined',0,0,'Undefined');""",
                (self._huntid, new_puz_id,))
            # sg.popup("Successful!")
        except Exception as e:
            sg.popup_error("Failed to add puzzle! Error:", e)
        self.db_get_puzzles()
        self.populate_puzzles()

    def _delete_puzzle(self):
        puz_idx = self._selected["Puzzle"]
        if puz_idx is None:
            sg.popup_error("No Puzzle selected!")
            return

        puzzle_data = self._data["Puzzles"][puz_idx]
        puz_id = puzzle_data[0]

        ans = sg.popup_yes_no(f"Are you sure you want to delete this puzzle: {puz_id}?")
        if ans == 'Yes':
            try:
                cursor = self.sql_db.cursor()
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_puzzles WHERE puzzleid = %s", (puz_id,))
                # sg.popup("Successful!")
            except Exception as e:
                sg.popup_error("Failed to delete puzzle! Error:", e)
        self.db_get_puzzles()
        self.populate_puzzles()

    def _update_puzzle(self, values):
        if self._selected["Puzzle"] is None:
            sg.popup_error("No puzzle selected!")
            return

        puzzle_data = self._data["Puzzles"][self._selected["Puzzle"]]
        puz_id = puzzle_data[0]

        new_puzzleid = values["-PUZZLE_ID_INP-"]
        new_name = values["-PUZZLE_NAME_INP-"]
        new_desc = values["-PUZZLE_DESC_INP-"]
        new_link = values["-PUZZLE_LINK_INP-"]
        new_points = values["-PUZZLE_POINTS_INP-"]
        new_req = values["-PUZZLE_REQPOINTS_INP-"]
        new_answer = values["-PUZZLE_ANSWER_INP-"]
        
        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunt_puzzles SET puzzleid=%s, name=%s, description=%s, relatedlink=%s, points=%s, requiredpoints=%s, answer=%s WHERE huntid=%s AND puzzleid=%s", 
            (new_puzzleid, new_name, new_desc, new_link, new_points, new_req, new_answer, self._huntid, puz_id))
            self.db_get_puzzles()
            self.populate_puzzles()
            sg.popup(f"Successfully updated puzzle {puz_id}!")
        except Exception as e:
            sg.popup("Failed to update puzzle. Error:", e)
    
    def _add_partial(self):
        if self._selected["Puzzle"] is None:
            sg.popup_error("No Puzzle selected!")
            return

        new_partial_trigger = sg.popup_get_text("Enter intermediate trigger phrase:")
        
        if new_partial_trigger == "Cancel":
            return
        if new_partial_trigger in [None, ""]:
            sg.popup_error("A phrase is required!")
            return
        
        new_partial_trigger = new_partial_trigger.lower().replace(" ", "")
        
        try:
            cursor = self.sql_db.cursor()
            cursor.execute("""INSERT INTO puzzledb.puzzlehunt_puzzle_partials 
                    (huntid,puzzleid,partialanswer,response) 
                    VALUES (%s,%s,%s,'You''re on the right track!');""",
                (self._huntid, self._data["Puzzles"][self._selected["Puzzle"]][0], new_partial_trigger))
            # sg.popup("Successful!")
        except Exception as e:
            sg.popup_error("Failed to add partial answer! Error:", e)
        self.db_get_puzzles()
        self.populate_puzzles(selected=self._selected["Puzzle"])

    def _delete_partial(self):
        puz_idx = self._selected["Puzzle"]
        if puz_idx is None:
            sg.popup_error("No Puzzle selected!")
            return

        partial_idx = self._selected["Partial"]
        if partial_idx is None:
            sg.popup_error("No Partial answer selected!")
            return

        puzzle_data = self._data["Puzzles"][puz_idx]
        puzzleid = puzzle_data[0]

        cursor = self.sql_db.cursor()
        cursor.execute("SELECT puzzleid, partialanswer, response FROM puzzledb.puzzlehunt_puzzle_partials WHERE puzzleid = %s", (puzzleid,))
        puzzle_partials = cursor.fetchall()

        if partial_idx >= len(puzzle_partials):
            return

        _, trigger, response = puzzle_partials[partial_idx]

        ans = sg.popup_yes_no(f"Are you sure you want to delete this partial answer: '{trigger}'' from puzzle: '{puzzleid}'?")
        if ans == 'Yes':
            try:
                cursor = self.sql_db.cursor()
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_puzzle_partials WHERE puzzleid = %s AND partialanswer = %s", (puzzleid, trigger))
                # sg.popup("Successful!")
            except Exception as e:
                sg.popup_error("Failed to delete partial answer! Error:", e)
        self.db_get_puzzles()
        self.populate_puzzles()
        
    def _update_partial(self, values):
        if self._selected["Puzzle"] is None:
            popup_error("No puzzle selected!")
            return
        puzzleid = self._data["Puzzles"][self._selected["Puzzle"]][0]

        new_trigger = values['-PARTIAL_TRIGGER_INP-']
        new_response = values['-PARTIAL_RESPONSE_INP-']

        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunt_puzzle_partials SET partialanswer=%s, response=%s WHERE huntid=%s AND puzzleid=%s", 
            (new_trigger, new_response, self._huntid, puzzleid))
            self.db_get_puzzles()
            self.populate_puzzles(selected=self._selected["Puzzle"], selected_partial=self._selected["Partial"])
            sg.popup(f"Successfully updated partial answer {new_trigger} for puzzle {puzzleid}!")
        except Exception as e:
            sg.popup("Failed to partial answer. Error:", e)

    def _update_team(self, values):
        if self._selected["Team"] is None:
            sg.popup_error("No team selected!")
            return

        team_data = self._data["Teams"][self._selected["Team"]]
        teamid = team_data[0]

        new_teamid = values["-TEAM_ID_INP-"]
        new_teamname = values["-TEAM_NAME_INP-"]
        new_hintcount = values["-TEAM_HINTS_INP-"]

        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunt_teams SET id=%s, teamname=%s, hintcount=%s WHERE huntid=%s AND id=%s", 
            (new_teamid, new_teamname, new_hintcount, self._huntid, teamid))
            self.db_get_teams()
            self.populate_teams()
            sg.popup(f"Successfully updated team {teamid}!")
        except Exception as e:
            sg.popup("Failed to update team. Error:", e)

    def _add_faq(self):
        faq_id = sg.popup_get_text("Type ID:")
        if faq_id in [faq[0] for faq in self._data["FAQ"]]:
            sg.popup_error("FAQ ID already exists. Select and update instead.")
            return
        
        try:
            cursor = self.sql_db.cursor()
            cursor.execute("""INSERT INTO puzzledb.puzzlehunt_faq 
                    (id,huntid,question,content) 
                    VALUES (%s,%s,'Undefined','Undefined');""",
                (faq_id, self._huntid,))
            # sg.popup("Successful!")
        except Exception as e:
            sg.popup_error("Failed to add FAQ! Error:", e)
        self.db_get_faq()
        self.populate_faq()

    def _delete_faq(self):
        faq_idx = self._selected["FAQ"]
        if faq_idx is None:
            sg.popup_error("No FAQ selected!")
            return

        line_data = self._data["FAQ"][faq_idx]
        faq_id = line_data[0]

        ans = sg.popup_yes_no(f"Are you sure you want to delete this FAQ: {faq_id}?")
        if ans == 'Yes':
            try:
                cursor = self.sql_db.cursor()
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_faq WHERE id = %s", (faq_id,))
                # sg.popup("Successful!")
            except Exception as e:
                sg.popup_error("Failed to delete FAQ! Error:", e)
        self.db_get_faq()
        self.populate_faq()

    def _update_faq(self, values):
        if self._selected["FAQ"] is None:
            sg.popup_error("No FAQ selected!")
            return

        faq_data = self._data["FAQ"][self._selected["FAQ"]]
        faq_id = faq_data[0]

        new_faqid = values["-FAQ_ID_INP-"]
        new_question = values["-FAQ_QSN_INP-"]
        new_answer = values["-FAQ_ANS_INP-"]

        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunt_faq SET id=%s, question=%s, content=%s WHERE huntid=%s AND id=%s", 
            (new_faqid, new_question, new_answer, self._huntid, faq_id))
            self.db_get_faq()
            self.populate_faq()
            sg.popup(f"Successfully updated FAQ {faq_id}!")
        except Exception as e:
            sg.popup("Failed to update FAQ. Error:", e)  
    
    def _add_erratum(self):
        puz_id = sg.popup_get_text("Type Puzzle ID to add erratum ('global' if not puzzle specific):")
        
        try:
            cursor = self.sql_db.cursor()
            cursor.execute("""INSERT INTO puzzledb.puzzlehunt_errata 
                    (huntid,puzzleid,content) 
                    VALUES (%s,%s,'Undefined');""",
                (self._huntid, puz_id,))
            # sg.popup("Successful!")
        except Exception as e:
            sg.popup_error("Failed to add erratum! Error:", e)
        self.db_get_errata()
        self.populate_errata()

    def _delete_erratum(self):
        erratum_idx = self._selected["Erratum"]
        if erratum_idx is None:
            sg.popup_error("No Erratum selected!")
            return

        line_data = self._data["Errata"][erratum_idx]
        erratum_id = line_data[0]

        ans = sg.popup_yes_no(f"Are you sure you want to delete this erratum: {erratum_id}?")
        if ans == 'Yes':
            try:
                cursor = self.sql_db.cursor()
                cursor.execute("DELETE FROM puzzledb.puzzlehunt_errata WHERE id = %s", (erratum_id,))
                # sg.popup("Successful!")
            except Exception as e:
                sg.popup_error("Failed to delete erratum! Error:", e)
        self.db_get_errata()
        self.populate_errata()

    def _update_erratum(self, values):
        if self._selected["Erratum"] is None:
            sg.popup_error("No Erratum selected!")
            return

        erratum_data = self._data["Errata"][self._selected["Erratum"]]
        erratum_id = erratum_data[0]

        new_erratumid = values["-ERR_ID_INP-"]
        new_puzzleid = values["-ERR_PUZ_INP-"]
        new_content = values["-ERR_TEXT_INP-"]

        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunt_errata SET id=%s, puzzleid=%s, content=%s WHERE huntid=%s AND id=%s", 
            (new_erratumid, new_puzzleid, new_content, self._huntid, erratum_id))
            self.db_get_errata()
            self.populate_errata()
            sg.popup(f"Successfully updated erratum {erratum_id}!")
        except Exception as e:
            sg.popup("Failed to update erratum. Error:", e)

    def _update_info_string(self, values):
        if self._selected["Info String"] is None:
            sg.popup_error("No Info String selected!")
            return

        info_data = self._data["Info Strings"][self._selected["Info String"]]
        info_domain, info_key, _ = info_data # huntid

        new_text = values["-INFO_TEXT_INP-"]

        cursor = self.sql_db.cursor()
        try:
            cursor.execute("UPDATE puzzledb.puzzlehunt_text_strings SET textstring=%s WHERE huntid=%s AND textkey=%s", 
            (new_text, info_domain, info_key))
            self.db_get_infostrings()
            self.populate_infostrings()
            sg.popup(f"Successfully updated info string {info_key}!")
        except Exception as e:
            sg.popup("Failed to update info string. Error:", e)

    def refresh_hunt_table(self):
        self.db_get_hunts()
        self.window["-HUNTIDTABLE-"].update(values=[[h] for h in self._data["Hunts"]])

    def db_get_hunts(self):
        cursor = self.sql_db.cursor()
        cursor.execute("SELECT * FROM puzzledb.puzzlehunts ORDER BY huntid;")
        hunts = cursor.fetchall()
        
        self._data["Hunts"] = []
        self._data["Hunt Info"] = []
        for _, huntid, name, theme, start_t, end_t in hunts:
            self._data["Hunts"].append(huntid)
            self._data["Hunt Info"].append(
                [
                    huntid, name or "", theme or "", start_t or "", end_t or ""
                ]
            )

    def db_get_puzzles(self):
        cursor = self.sql_db.cursor()
        cursor.execute("SELECT puzzleid, name, description, relatedlink, points, requiredpoints, answer FROM puzzledb.puzzlehunt_puzzles WHERE huntid = %s ORDER BY puzzleid;", (self._huntid,))
        self._data["Puzzles"] = cursor.fetchall()

    def db_get_teams(self):
        cursor = self.sql_db.cursor()
        cursor.execute("""
        SELECT teamsolves.teamid AS teamid, teamsolves.teamname AS teamname, 
            MAX(teamsolves.last_solvetime) AS last_solvetime, COALESCE(SUM(puzzles.points), 0) AS total_points,
            teamsolves.teamhintcount AS teamhintcount FROM
                (SELECT teams.id AS teamid, teams.teamname AS teamname, MAX(solves.solvetime) AS last_solvetime, solves.puzzleid as puzzleid,
                    teams.huntid AS huntid, teams.hintcount AS teamhintcount FROM puzzledb.puzzlehunt_teams teams
                LEFT JOIN puzzledb.puzzlehunt_solves solves
                    ON solves.teamid = teams.id AND solves.huntid = teams.huntid
                    GROUP BY teams.id, solves.puzzleid) teamsolves
        LEFT JOIN puzzledb.puzzlehunt_puzzles puzzles
        ON teamsolves.puzzleid = puzzles.puzzleid AND teamsolves.huntid = puzzles.huntid
        WHERE teamsolves.huntid = %s
        GROUP BY teamsolves.teamid, teamsolves.teamname, teamsolves.teamhintcount
        ORDER BY teamsolves.teamname;""", (self._huntid,))
        self._data["Teams"] = cursor.fetchall()

    def db_get_faq(self):
        cursor = self.sql_db.cursor()
        cursor.execute("SELECT id, question, content FROM puzzledb.puzzlehunt_faq WHERE huntid = %s ORDER BY question;", (self._huntid,))
        self._data["FAQ"] = cursor.fetchall()

    def db_get_errata(self):
        cursor = self.sql_db.cursor()
        cursor.execute("SELECT id, puzzleid, content FROM puzzledb.puzzlehunt_errata WHERE huntid = %s ORDER BY puzzleid, content;", (self._huntid,))
        self._data["Errata"] = cursor.fetchall()

    def db_get_infostrings(self):
        cursor = self.sql_db.cursor()
        cursor.execute("SELECT huntid, textkey, textstring FROM puzzledb.puzzlehunt_text_strings WHERE huntid IN ('system', %s) ORDER BY huntid, textkey;", (self._huntid,))
        self._data["Info Strings"] = cursor.fetchall()

    def populate_huntinfo(self):
        huntinfo = self._data["Hunt Info"][self._data["Hunts"].index(self._huntid)]
        huntid, name, theme, start_t, end_t = huntinfo

        self.window["-HUNTINFO_ID_INP-"].update(value=huntid)
        self.window["-HUNTINFO_NAME_INP-"].update(value=name or "")
        self.window["-HUNTINFO_THEME_INP-"].update(value=theme or "")
        self.window["-HUNTINFO_STARTTIME_INP-"].update(value=start_t or "")
        self.window["-HUNTINFO_ENDTIME_INP-"].update(value=end_t or "")

    def populate_puzzles(self, selected=0, selected_partial=0):
        puzzle_data = self._data["Puzzles"]
        self.window["-PARTIALS_TABLE-"].update([])
        self.fill_partial_input("","","")

        if selected >= len(puzzle_data):
            self.window["-PUZZLES_TABLE-"].update(values=puzzle_data)
            return
        
        self.window["-PUZZLES_TABLE-"].update(values=puzzle_data, select_rows=[selected])
        
        self._selected["Puzzle"] = selected

        puzzleid, name, desc, link, points, req, answer = puzzle_data[selected]

        self.fill_puzzle_input(puzzleid, name, desc, link, points, req, answer)

        cursor = self.sql_db.cursor()
        cursor.execute("SELECT puzzleid, partialanswer, response FROM puzzledb.puzzlehunt_puzzle_partials WHERE puzzleid = %s ORDER BY puzzleid, partialanswer", (puzzleid,))
        puzzle_partials = cursor.fetchall()
        if puzzle_partials:
            if selected_partial is None or selected_partial >= len(puzzle_partials):
                self.window["-PARTIALS_TABLE-"].update(puzzle_partials)
                return

            self.window["-PARTIALS_TABLE-"].update(puzzle_partials, select_rows=[selected_partial])

            puzid, trigger, response = puzzle_partials[selected_partial]
            self.fill_partial_input(puzid, trigger, response)

    def populate_teams(self, selected=0):
        if selected >= len(self._data["Teams"]):
            self.window["-TEAMS_TABLE-"].update(values=self._data["Teams"])
            return
        
        self.window["-TEAMS_TABLE-"].update(values=self._data["Teams"], select_rows=[selected])
        
        self._selected["Team"] = selected
        
        teamid, teamname, _, _, hintcount = self._data["Teams"][selected]

        self.fill_team_input(teamid, teamname, hintcount)

        cursor = self.sql_db.cursor()
        cursor.execute("SELECT id FROM puzzledb.puzzlehunt_solvers WHERE teamid = %s", (teamid,))
        members = cursor.fetchall()
    
        cursor.execute("SELECT puzzleid, solvetime FROM puzzledb.puzzlehunt_solves WHERE teamid = %s ORDER BY solvetime DESC", (teamid,))
        solves = cursor.fetchall()

        cursor.execute("SELECT puzzleid, attempt, solvetime FROM puzzledb.puzzlehunt_attempts WHERE teamid = %s ORDER BY solvetime DESC", (teamid,))
        attempts = cursor.fetchall()

        self.window["-TEAM_MEMBERS_TABLE-"].update(values=members)
        self.window["-TEAM_SOLVES_TABLE-"].update(values=solves)
        self.window["-TEAM_ATTEMPTS_TABLE-"].update(values=attempts)

    def populate_faq_and_errata(self):
        self.populate_faq()
        self.populate_errata()

    def populate_faq(self, selected=0):
        if selected >= len(self._data["FAQ"]):
            self.window["-FAQ_TABLE-"].update(values=self._data["FAQ"])
            return
        
        self.window["-FAQ_TABLE-"].update(values=self._data["FAQ"], select_rows=[selected])

        self._selected["FAQ"] = selected
        
        line_data = self._data["FAQ"][selected]
        faqid, question, answer = line_data
        self.fill_faq_input(faqid, question, answer)

    def populate_errata(self, selected=0):
        if selected >= len(self._data["Errata"]):
            self.window["-ERRATA_TABLE-"].update(values=self._data["Errata"])
            return
        
        self.window["-ERRATA_TABLE-"].update(values=self._data["Errata"], select_rows=[selected])

        self._selected["Erratum"] = selected
        
        line_data = self._data["Errata"][selected]
        errid, puzid, content = line_data
        self.fill_errata_input(errid, puzid, content)

    def populate_infostrings(self, selected=0):
        if selected >= len(self._data["Info Strings"]):
            self.window["-INFOSTRINGS_TABLE-"].update(values=self._data["Info Strings"])
            return

        self.window["-INFOSTRINGS_TABLE-"].update(values=self._data["Info Strings"], select_rows=[selected])
        
        self._selected["Info String"] = selected
        
        domain, key, text = self._data["Info Strings"][selected]
        self.fill_infostring_input(domain, key, text)


    def fill_huntinfo_input(self, huntid, name, theme, start_t, end_t):
        self.window["-HUNTINFO_ID_INP-"].update(value=huntid)
        self.window["-HUNTINFO_NAME_INP-"].update(value=name)
        self.window["-HUNTINFO_THEME_INP-"].update(value=theme)
        self.window["-HUNTINFO_STARTTIME_INP-"].update(value=start_t)
        self.window["-HUNTINFO_ENDTIME_INP-"].update(value=end_t)

    def fill_puzzle_input(self, puzzleid, name, desc, link, points, req, answer):
        self.window["-PUZZLE_ID_INP-"].update(value=puzzleid)
        self.window["-PUZZLE_NAME_INP-"].update(value=name)
        self.window["-PUZZLE_DESC_INP-"].update(value=desc)
        self.window["-PUZZLE_LINK_INP-"].update(value=link)
        self.window["-PUZZLE_POINTS_INP-"].update(value=points)
        self.window["-PUZZLE_REQPOINTS_INP-"].update(value=req)
        self.window["-PUZZLE_ANSWER_INP-"].update(value=answer)

    def fill_team_input(self, teamid, teamname, hintcount):
        self.window["-TEAM_ID_INP-"].update(value=teamid)
        self.window["-TEAM_NAME_INP-"].update(value=teamname)
        self.window["-TEAM_HINTS_INP-"].update(value=hintcount)
    
    def fill_faq_input(self, faqid, question, answer):
        self.window["-FAQ_ID_INP-"].update(value=faqid)
        self.window["-FAQ_QSN_INP-"].update(value=question)
        self.window["-FAQ_ANS_INP-"].update(value=answer)

    def fill_errata_input(self, errid, puzid, content):
        self.window["-ERR_ID_INP-"].update(value=errid)
        self.window["-ERR_PUZ_INP-"].update(value=puzid)
        self.window["-ERR_TEXT_INP-"].update(value=content)

    def fill_infostring_input(self, domain, key, text):
        self.window["-INFO_DOMAIN_INP-"].update(value=domain)
        self.window["-INFO_KEY_INP-"].update(value=key)
        self.window["-INFO_TEXT_INP-"].update(value=text)

    def fill_partial_input(self, puzid, trigger, response):
        self.window["-PARTIAL_PUZZLE_INP-"].update(value=puzid)
        self.window["-PARTIAL_TRIGGER_INP-"].update(value=trigger)
        self.window["-PARTIAL_RESPONSE_INP-"].update(value=response)

    def _direct_query(self):
        query = sg.popup_get_text("[DANGER] Directly query the database. Hope you know what you're doing.")
        if query == "Cancel":
            return
        try:
            self.sql_db.cursor().execute(query)
            sg.popup("Successful!")
        except Exception as e:
            sg.popup_error("Query failed! Error:", e)



if __name__ == '__main__':
    PuzzlehuntGUI().run()
