import random
import time
import hashlib
import urllib.parse
import requests


class XimalayaSign:
    @staticmethod
    def _md5(text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    @staticmethod
    def _random_int(max_val: int) -> int:
        return random.randint(0, max_val - 1)

    @staticmethod
    def get_sign() -> str:
        # Get current timestamp in milliseconds
        current_time = int(time.time() * 1000)

        # Generate components
        prefix = "himalaya-"
        timestamp = str(current_time)
        # Adding arbitrary offset to create future timestamp
        future_timestamp = str(int(time.time()))

        # Create the initial string with random numbers
        rand1 = XimalayaSign._random_int(100)
        rand2 = XimalayaSign._random_int(100)

        # Format: {himalaya-<timestamp>}(<rand1>)<timestamp>(<rand2>)<future_timestamp>
        initial_string = f"{{{prefix}{timestamp}}}({rand1}){timestamp}({rand2}){future_timestamp}"
        print(XimalayaSign._md5(initial_string))
        # Replace the {himalaya-<timestamp>} part with its MD5 hash
        import re
        def replace_with_md5(match):
            return XimalayaSign._md5(match.group(1))

        final_string = re.sub(r'{([\w-]+)}', replace_with_md5, initial_string)
        return final_string

xm = XimalayaSign()
def get_header():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36"
    }
    xm_sign = xm.get_sign()
    headers['xm-sign'] = "D2UkzxFXB19lk62EKS4FFr6bCot3Q8RVKAnu0eR++wDW0Xb8&&nnIZ0LVpyT2kiq93ccE7QqeiSt2UC5hjBrlxyqpnIWk_1"
    return headers


# Example usage
if __name__ == "__main__":
    # Generate a sign
    sign = XimalayaSign.get_sign()
    print(f"Generated sign: {sign}")

    url = "https://www.ximalaya.com/revision/search/main?core=all&spellchecker=true&device=iPhone&kw=%E9%9B%AA%E4%B8%AD%E6%82%8D%E5%88%80%E8%A1%8C&page=1&rows=20&condition=relation&fq=&paidFilter=false"
    headers = get_header()
    s = requests.get(url, headers=headers, verify=False)
    print(s.json())