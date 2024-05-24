import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import concat, lit, split, udf, from_unixtime, col
from pyspark.sql.types import StringType, ArrayType
from pyspark import SparkFiles
import json
import ast
import re
import os
from kestra import Kestra

# define a function to identify the exact type of reddit data extracted from each entry
def identify_type(type):
    if type=="t3":
        return "post"
    elif type=="t1":
        return "comment"
    else:
        return None

# Register the custom function as a UDF
identify_type_udf = udf(lambda x:identify_type(x), StringType())

# initialise spark context and spark session
sc = pyspark.SparkContext(appName="reddit_preprocessing")
spark = SparkSession.builder \
    .appName("reddit_preprocessing") \
    .getOrCreate()

# create a regular expression to search for JSON files
pattern = r".+\.json$"

# compile the regular expression pattern
regex = re.compile(pattern)

# get root directory where the submitted files are stored
root_dir = SparkFiles.getRootDirectory()

# list the files and obtain the name of the raw reddit data json
for filename in os.listdir(root_dir):
    # Check if the filename matches the pattern
    if regex.match(filename):
        reddit_json_file = filename
        reddit_json_dir = f'{root_dir}/{filename}'
        break
    

raw_df = sc.wholeTextFiles(reddit_json_dir).map(lambda x:ast.literal_eval(x[1]))\
                            .map(lambda x: json.dumps(x))

raw_df = spark.read.json(raw_df)

# convert the author column from a StringType into an ArrayType to standardize the schema. This is to accomodate for the gnews data which returns an array of authors
new_df = raw_df.withColumn("author", split(col("author"), ",").cast(ArrayType(StringType())))

# split the name column into a type column but disregard the ID
new_df = new_df.withColumn("type", split(new_df["name"], "_")[0])

# convert the permalink values into actual links that link to the actual post and comment
new_df = new_df.withColumn("permalink", concat(lit("https://www.reddit.com"), new_df["permalink"]))

# convert the unixtime to the datatime format (YY-MM-DD HH-mm-ss)
new_df = new_df.withColumn("datetime", from_unixtime("unix_time"))

# identify the exact type of reddit data that was extracted from the api i.e post or comment
new_df = new_df.withColumn("type", identify_type_udf(new_df["type"]))

# delete the columns which are no longer needed with the addition of the other features.
new_df = new_df.drop("name")
new_df = new_df.drop("score")
new_df = new_df.drop("unix_time")

# change the names of the columns 
# (author->authors)
# (body->content)
# (permalink->url)
# (post_title->context)

new_df = new_df.withColumnsRenamed({'author': 'authors', 
                                    'body': 'content',
                                    'permalink': 'url',
                                    'post_title':'context',
                                    })

preprocessed_json = new_df.toJSON().collect()[:5]

Kestra.outputs({'test': 'value', 'int': 2, 'bool': True, 'float': 3.65})


# define the parameters for the kafka broker and topic
kafka_params = {
    "kafka.bootstrap.servers": "kafka:9092",  # Kafka broker address
    "topic": "reddit_post_preprocessed"  # Kafka topic name
}

# write data to Kafka
for message in preprocessed_json:
    spark \
        .createDataFrame([message], StringType()) \
        .write \
        .format("kafka") \
        .options(**kafka_params) \
        .save()