import enum
import math

# This graph will determine which free agents a team can sign based on their available cap space 
# and which players they should sign based on their needs and other player factors

class LeagueRules(enum.Enum):  # Fixed the base class
    POSTION_LIST = ["QB", "RB", "WR", "TE"]
    MIN_PLAYER_AT_POSITION = {
            "QB": 1,
            "RB": 1,
            "WR": 2,
            "TE": 1,
        }
    SALARY_CAP = 2000000

class FootballPlayer:
    def __init__(self, name, position, expected_salary, madden_rating, available=True):
        self.name = name
        self.position = position
        self.expected_salary = expected_salary
        self.madden_rating = madden_rating
        self.available = available
        self.player_value = (self.madden_rating / self.expected_salary) * 100000
    
    def get_availability(self):
        return self.available
    
class FootballTeam:
    def __init__(self, team_name):
        self.team_name = team_name
        self.roster = {}
        for position in LeagueRules.POSTION_LIST.value:
            self.roster[position] = []
        self.cap_space = LeagueRules.SALARY_CAP.value
    
    def can_sign_player(self, player):
        if player.expected_salary <= self.cap_space and player.get_availability():
            return True
        return False
    
    # A team wants to sign a player if the player can provide more value than the lowest value player at thier position
    def check_if_team_wants_players(self, player):
        lowest_rostered_value_at_pos = self.get_lowest_value_at_position(player.position)
        if player.player_value > lowest_rostered_value_at_pos:
            # print(f"Team {self.team_name} wants player {player.name} with value {player.player_value}. Lowest value is {lowest_rostered_value_at_pos}.")
            return True
        return False

    def get_lowest_value_at_position(self, position):
        min_value = math.inf
        for player in self.roster[position]:
            if player.player_value < min_value:
                min_value = player.player_value
        
        return min_value
    
    def sign_player(self, player):
        if self.can_sign_player(player):
            #self.roster.append(player)
            self.roster[player.position].append(player)
            self.cap_space -= player.expected_salary
            player.available = False
            return True
        return False
    
    def get_available_players(self):
        return [player for player in self.roster if player.get_availability()]
    
    def get_cap_space(self):
        return self.cap_space
    
    def get_num_player_needed(self, position):
        current_qbs = [player for player in self.roster[position]]
        num_players_needed = LeagueRules.MIN_PLAYER_AT_POSITION.value[position] - len(current_qbs)
        return num_players_needed
    
    def get_remaining_cap_space(self):
        total_salary = sum(player.expected_salary for player in self.roster)
        return self.cap_space - total_salary