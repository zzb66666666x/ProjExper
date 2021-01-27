from database import DataBase
import ASM
from schema import *
import Data2

# Here, because the data provided by the professor has no Actor Award satisfied the original year required by the Query, 2000,
# (you can easily checked form the provided data on BB, the Actor Award table is not long)
# the result of the original query should be empty list.
# So we change the year to 1993

'''
TEST FILE FOR E2 Query 2
List all ‘comedy’ movies that have been suggested for a US award in 1993 for one of their actors 
provided this actor has never played in an ‘action’ movie nor written or directed an Italian movie.

PLEASE MAKE SURE YOU HAVE READ THE GRAMMAR FILE IF YOU WANT TO TEST MORE ABOUT THE QUERY.
'''

db = DataBase(list(relation_schema.keys()))
a = ASM.ASM(db)
Data2.insertData(db)

# Notice:
#   If you want somthing to be a constant string, please add @ before it,
#   example1: @18 instead of 18, 
#             because 18 would be convert to float
#   example2: @RESTRICTION instead of RESTRICTION, 
#             because the latter one would be a list of entries and could not be used for searching using index structure

# If you add 0 after a.Run(), the result would not print out.

# For E2(ii) / E3(v), you should only comment one because the assignment can not be repeated.
# For justification, you can use SQL to do the same query of the provided data on BB and compare the result with our result, which is the same.
# You can check the correction of E3(v) roughly that the result of it are the same with the result of E2(ii) (Although data has different order)

# The test for E2(ii)
a.Run("q0 = (MOVIE where (self.MOVIE_genre == comedy))",0)
a.Run("q1 = (ACTOR_AWARD where ((self.ACTOR_AWARD_year == 1993) and (self.ACTOR_AWARD_result == nominated)))",0)
a.Run("q2 = (AWARD where (self.AWARD_country == USA))",0)
a.Run("q3 = ((q1 cross q2) where (self.ACTOR_AWARD_name == self.AWARD_name))",0)
a.Run("q4 = ((q0 cross q3) where ((self.MOVIE_title = self.ACTOR_AWARD_title) and (self.MOVIE_year = self.ACTOR_AWARD_M_year)))",0)
a.Run("q5 = ((q4 cross ROLE) where ((self.ACTOR_AWARD_title == self.ROLE_movie) and (self.ACTOR_AWARD_M_year == self.ROLE_year) and (self.ACTOR_AWARD_description == self.ROLE_description))",0)
a.Run("q6 = (MOVIE where (self.MOVIE_country == Italy))",0)
a.Run("q7 = ((WRITER cross MOVIE) where ((self.WRITER_title == self.MOVIE_title) and (self.WRITER_year == self.MOVIE_year)))",0)
a.Run("q8 = ((DIRECTOR cross MOVIE) where ((self.DIRECTOR_title == self.MOVIE_title) and (self.DIRECTOR_year == self.MOVIE_year)))",0)
a.Run("q9 = (MOVIE where (self.MOVIE_genre == action))",0)
a.Run("q10 = ((ROLE cross q9) where ((self.ROLE_movie == self.MOVIE_title) and (self.ROLE_year == self.MOVIE_year)))",0)
a.Run("q11 = q5 where (not ((self.ROLE_id in q7.WRITER_id) or (self.ROLE_id in q8.DIRECTOR_id) or (self.ROLE_id in q10.ROLE_id)))",0)
a.Run("distinct (q11.MOVIE_title)")

# The test for E3(v)
# using index structure
'''
a.Run("q0 = (@MOVIE search {'MOVIE_genre':'comedy'})",0)
a.Run("q1 = (@ACTOR_AWARD search {'ACTOR_AWARD_year':1993,'ACTOR_AWARD_result':'nominated'})",0)
a.Run("q2 = (AWARD where (self.AWARD_country == USA))",0)
a.Run("q3 = ((q1 cross q2) where (self.ACTOR_AWARD_name == self.AWARD_name))",0)
a.Run("q4 = ((q0 cross q3) where ((self.MOVIE_title = self.ACTOR_AWARD_title) and (self.MOVIE_year = self.ACTOR_AWARD_M_year)))",0)
a.Run("q5 = ((q4 cross ROLE) where ((self.ACTOR_AWARD_title == self.ROLE_movie) and (self.ACTOR_AWARD_M_year == self.ROLE_year) and (self.ACTOR_AWARD_description == self.ROLE_description))",0)
a.Run("q6 = (@MOVIE search {'MOVIE_country':'Italy'})",0)
a.Run("q7 = ((WRITER cross MOVIE) where ((self.WRITER_title == self.MOVIE_title) and (self.WRITER_year == self.MOVIE_year)))",0)
a.Run("q8 = ((DIRECTOR cross MOVIE) where ((self.DIRECTOR_title == self.MOVIE_title) and (self.DIRECTOR_year == self.MOVIE_year)))",0)
a.Run("q9 = (@MOVIE search {'MOVIE_genre':'action'})",0)
a.Run("q10 = ((ROLE cross q9) where ((self.ROLE_movie == self.MOVIE_title) and (self.ROLE_year == self.MOVIE_year)))",0)
a.Run("q11 = q5 where (not ((self.ROLE_id in q7.WRITER_id) or (self.ROLE_id in q8.DIRECTOR_id) or (self.ROLE_id in q10.ROLE_id)))",0)
a.Run("distinct (q11.MOVIE_title)")
'''