-- Reduce APRS-IS data using Pig and Hadoop.
-- NOTE: This code requires Pig 0.11.1 or better. It is known to FAIL with 0.9.2.
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.
--
-- Copyright (c) 2013 Alan Crosswell

-- My UDF that parses APRS-IS lines and positions
Register 's3n://aprs-is/code/aprspig.py' using jython as myudf;

-- the test file, small-sample.log is about 40,000 lines.
-- raw = LOAD 's3n://aprs-is/small-sample.log' USING TextLoader as (line:chararray);

-- one actual log file, bzip2 compressed:
-- raw = LOAD 's3n://aprs-is/aprsis-20110101.log.bz2' USING TextLoader as (line:chararray);

-- all the log files, bzip2 compressed:
raw = LOAD 's3n://aprs-is/aprsis-*' USING TextLoader as (line:chararray);

-- Parse the lines into aprs fields.
aprs = FOREACH raw GENERATE FLATTEN(myudf.aprs(line));
DESCRIBE aprs;

-- Filter out useless data such as firsthop WIDEn-N
useful = FILTER aprs BY NOT ((firsthop MATCHES 'WIDE.*'));

-- Parse the various position formats into canonical form
aprspos = foreach useful generate firsthop,from_call,flatten(myudf.position(to_call,info));
describe aprspos;

-- Keep only valid positions: There are many other non-position packets.
goodpos = FILTER aprspos BY latitude is not null;

-- Drop fields we are ignoring (for now) such as ambiguity, course, speed.
projectpos = FOREACH goodpos GENERATE firsthop,from_call,latitude,longitude;

-- Eliminate duplicates
distinctpos = DISTINCT projectpos PARALLEL 50;

-- Group positions reported around their first hop digipeater.
firsthops = GROUP distinctpos by (firsthop) PARALLEL 50;
DESCRIBE firsthops;

-- eliminate the duplicative firsthop key that is both the group field and firsthop field in each tuple in the bag.
firsts = FOREACH firsthops {
	pos = FOREACH projectpos GENERATE from_call,latitude,longitude;
	GENERATE group as firsthop, pos;
	};
describe firsts;

-- Each record has a firsthop key and then a bag of positions.

-- Store the full reduced dataset:
STORE firsts INTO 's3n://aprs-is/reduced/firsthops' using PigStorage();

-- Tried and store this as a JSON file to make it a little bit easier to parse.
-- However, there appears to be a bug with doing this.
-- STORE firsts INTO 's3n://aprs-is/reduced/firsthops.json' using JsonStorage();
