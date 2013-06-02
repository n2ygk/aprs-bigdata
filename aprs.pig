-- simple APRS-IS demo. Uses a Python parser found in myudf.py
-- the test file, small-sample.log is about 40,000 lines.
-- Register 's3n://n2ygk/aprspig.py' using jython as myudf;
Register '/home/hadoop/aprspig.py' using jython as myudf;
-- raw = LOAD 'small-sample.log' USING TextLoader as (line:chararray);
-- raw = LOAD 's3n://aprs-is/small-sample.log' USING TextLoader as (line:chararray);
-- duh
raw = LOAD '/home/hadoop/s.log' USING TextLoader as (line:chararray);
-- limit to 1000 rows for now
cooked = LIMIT raw 1000;
aprs = FOREACH cooked GENERATE FLATTEN(myudf.aprs(line));
DESCRIBE aprs;
useful = FILTER aprs BY NOT ((firsthop MATCHES 'WIDE.*'));
firsthops = GROUP useful by (firsthop) PARALLEL 50;
DESCRIBE firsthops;
STORE firsthops INTO '/home/hadoop/aprs' using PigStorage();
-- STORE firsthops INTO 's3n://n2ygk/aprs' using PigStorage();




