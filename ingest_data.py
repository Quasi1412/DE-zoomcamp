import argparse, subprocess, sys
import pandas as pd
import pyarrow.parquet as pq
from time import time
from sqlalchemy import create_engine


def main(params):
    
    url  = params.url
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    
    #get the name of the file from url
    file_name = url.rsplit('/',1)[-1].strip()
    print(f'Downloading the file {file_name}')
    
    #download the file with the subprocess
    subprocess.run(['curl', url, '-o',file_name],check= True)
    print('\n')
    
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    
    if '.parquet' in file_name:
        file = pq.ParquetFile(file_name)
        df = next(file.iter_batches(batch_size=10)).to_pandas()
        df_iter = file.iter_batches(batch_size=100000)
    elif '.csv' in file_name:
        df = pd.read_csv(file_name, nrows=10)
        df_iter = pd.read_csv(file_name, iterator=True, chunksize=100000)
    else:
        print(f'Error only .csv or .parquet files are allowed')
        sys.exit()
        
    df.head(0).to_sql(name=table_name,con = engine,if_exists='replace' )
    
    
    #Insert_values
    start_time = time()
    count = 0
    
    for batch in df_iter:
        count += 1
        
        if '.parquet' in file_name:
            batch_df = batch.to_pandas()
        else:
            batch_df = batch
            
        print(f'inserting batch {count}...')
        
        b_start = time()
        batch_df.to_sql(name = table_name, con = engine, if_exists = 'append')
        b_end = time()
        
        print(f'Inserted!! Time taken is {b_end - b_start}')
        
    end_time = time()
    print(f'Values have been inserted into PostgreSQL DB!! Time Taken: {end_time-start_time}')
    

if __name__=='__main__':
    
    parser = argparse.ArgumentParser(description='Loading data from parquet or csv file and linking to postgreSQL DB:')
    parser.add_argument('--user',help='Username for Postgres')
    parser.add_argument('--password', help='Password for postgres')
    parser.add_argument('--host',help='Hostname for postgres')
    parser.add_argument('--port', help='Port number for postgre')
    parser.add_argument('--db', help='Database name in Postgre')
    parser.add_argument('--table_name', help='Table name in Postgre')
    parser.add_argument('--url',help='URL for the .parquet/.csv file')
    
    args = parser.parse_args()
    main(args)         