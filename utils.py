from dotenv import load_dotenv
from enum import Enum
import finnhub
import os
from memory_profiler import memory_usage
import time
from functools import wraps

load_dotenv()

finnhub_client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))

class FinnhubConcept(Enum):

    PROFIT = 'us-gaap_NetIncomeLoss'
    SHARES = 'us-gaap_WeightedAverageNumberOfDilutedSharesOutstanding'
    EPS = 'us-gaap_EarningsPerShareDiluted'

def extract_concept(quarter, concept):
    quarter = [
        *quarter['report']['ic'],
        *quarter['report']['bs'],
        *quarter['report']['cf']
    ]
    concept = FinnhubConcept[concept.upper()].value

    try:
        return next(
            item for item in quarter
            if item['concept'] == concept
        )['value']
    except StopIteration:
        return None



def time_and_memory_profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        mem_before = memory_usage()[0]

        result = func(*args, **kwargs)

        mem_after = memory_usage()[0]
        end_time = time.perf_counter()

        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        print(f"{func.__name__} used {mem_after - mem_before:.4f} MiB")
        return result
    return wrapper

