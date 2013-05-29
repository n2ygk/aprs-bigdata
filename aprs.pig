-- simple APRS-IS demo. Uses a Python parser found in myudf.py
-- the test file, small-sample.log is about 40,000 lines.
Register 'myudf.py' using jython as myudf;
-- raw = LOAD 'small-sample.log' USING TextLoader as (line:chararray);
raw = LOAD 's3n://aprs-is/small-sample.log' USING TextLoader as (line:chararray);
-- limit to 10 rows for now
LIMIT raw 10;
aprs = FOREACH raw GENERATE FLATTEN(myudf.aprs(line));
DESCRIBE aprs;
firsthops = GROUP aprs by (firstheard) PARALLEL 50;
DESCRIBE firsthops;
STORE firsthops INTO '/tmp/aprs';



