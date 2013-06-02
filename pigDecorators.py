__author__="Alan Crosswell <alan@columbia.edu>"
"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Copyright (c) 2013 Alan Crosswell
"""
def outputSchema(schema):
  """
  allow friendly use of your code outside the Pig context by defining a decorator that
  returns the results as a dict.

  Add this to your code:
  if 'outputSchema' not in locals():
    from pigDecorators import *
  """
  sch = []
  for s in schema.split(','):
    name,type = s.split(':')
    sch.append(name)
  def wrapper(func):
    def impl(*args, **kwargs):
      keyz = {}
      r = func(*args, **kwargs)
      if not r: return None
      for n in range(len(r)):
        keyz[sch[n]] = r[n]
      return keyz
    return impl
  return wrapper
