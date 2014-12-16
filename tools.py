"""A bunch of functions that are used by multiple threads.
"""
import pt, hashlib, re, subprocess, time, copy, networking, custom, logging, random
from json import dumps as package, loads as unpackage
from urllib import urlopen
import re
#print(json.dumps(x, indent=3, sort_keys=True))  for pretty printing
def getPublicIp():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    # data = '<html><head><title>Current IP Check</title></head><body>Current IP Address: 65.96.168.198</body></html>\r\n'
    return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
def int2hash(a): return buffer_(str(hex(a))[2:], 64)
def hash2int(a): return int(str(a), 16)
def cost_0(txs, address):
    #cost of the zeroth confirmation transactions
    total_cost = []
    txs=filter(lambda t: address == addr(t), txs)
    txs=filter(lambda t: t['type']=='spend', txs)
    for t in txs:
        total_cost.append(t['fee'])
        total_cost.appnd(t['amount'])
    return sum(total_cost)
def block_fee(length): return 10**9#total blocks is all_money divided by this. 21000000 blocks in this case
#assume it takes 0.5 seconds to process each block. If someone with 1% money does DDOS, total_blocks/200 seconds is how long they can. I am aiming for 1% of money to be able to DDOS for 1 day.
#since each block can be 10 kb, total block length is total_blocks*10kB. I am aiming for 210 GB.
#once we apply mini-blockchain proposal, then this number will shrink slowly. The total coins will decrease by a half-life ever 21 million blocks.
def fee_check(tx, txs, DB):
    address = addr(tx)
    cost=cost_0(txs+[tx], address)
    acc=db_get(address, DB)
    if int(acc['amount']) < cost: 
        log('insufficient money')
        return False
    return True
def entropy(txs):
    one=0
    zero=0
    for t in filter(lambda x: x['type']=='sign', txs):
        if t['entropy']==0:
            zero+=len(t['jackpots'])
        elif t['entropy']==1:
            one+=len(t['jackpots'])
        else:
            error()
    if one>zero: return 1
    else: return 0
def get_(loc, thing): 
    if loc==[]: return thing
    return get_(loc[1:], thing[loc[0]])
def set_(loc, dic, val):
    get_(loc[:-1], dic)[loc[-1]] = val
    return dic
def adjust(pubkey, DB, f):#location shouldn't be here.
    acc = db_get(pubkey, DB)
    f(acc)
    db_put(pubkey, acc, DB)    
def adjust_int(key, pubkey, amount, DB, add_block):
    def f(acc, amount=amount):
        if not add_block: amount=-amount
        set_(key, acc, (get_(key, acc) + amount))
    adjust(pubkey, DB, f)
def adjust_string(location, pubkey, old, new, DB, add_block):
    def f(acc, old=old, new=new):
        current=get_(location, acc)
        if add_block: 
            set_(location, acc, new)
        else: set_(location, acc, old)
    adjust(pubkey, DB, f)
def adjust_dict(location, pubkey, remove, dic, DB, add_block):
    def f(acc, remove=remove, dic=dic):
        current=get_(location, acc)
        if remove != add_block:# 'xor' and '!=' are the same.
            current=dict(dic.items() + current.items())
        else: 
            try:
                current.pop(dic.keys()[0])
            except:
                log('current dic: ' +str(current) + ' ' +str(dic)+' '+str(location))
        set_(location, acc, current)
    adjust(pubkey, DB, f)    
def adjust_list(location, pubkey, remove, item, DB, add_block):
    def f(acc, remove=remove, item=item):
        current=get_(location, acc)
        if remove != (add_block):# 'xor' and '!=' are the same.
            current.append(item)
        else: 
            current.remove(item)
        set_(location, acc, current)
    adjust(pubkey, DB, f)    
def symmetric_put(id_, dic, DB, add_block):
    if add_block: db_put(id_, dic, DB)
    else: db_delete(id_, DB)
def empty_peer(): return {'blacklist':0, 'lag':40.0, 'length':0, 'diffLength':"0"}
def peer_split(peer):
    a=peer.split(':')
    a[1]=int(a[1])
    return a
def port_grab(peer): return peer_split(peer)[1]
def add_peer(peer, current_peers=0):
    if current_peers==0:
        current_peers=local_get('peers')
    if peer in current_peers.keys():
        return False
    a=empty_peer()
    a['port']=port_grab(peer)
    current_peers[peer]=a
    local_put('peers', current_peers)
def dump_out(queue):
    while not queue.empty():
        try:
            queue.get(False)
        except:
            pass
logging.basicConfig(filename=custom.log_file, level=logging.INFO)
def log(junk):
    if isinstance(junk, Exception):
        logging.exception(junk)
    else:
        logging.info(str(junk))
def can_unpack(o):
    try:
        unpackage(o)
        return True
    except:
        return False
def addr(tx): return make_address(tx['pubkeys'], len(tx['signatures']))
def sign(msg, privkey): return pt.ecdsa_sign(msg, privkey)
def verify(msg, sig, pubkey): return pt.ecdsa_verify(msg, sig, pubkey)
def privtopub(privkey): return pt.privtopub(privkey)
def hash_(x): return hashlib.sha384(x).hexdigest()[0:64]
def det_hash(x):
    """Deterministically takes sha256 of dict, list, int, or string."""
    #x=unpackage(package(x))
    #log('in det hash: ' +str(package(x, sort_keys=True)))
    return hash_(package(x, sort_keys=True))
def POW(block):
    h=det_hash(block)
    block[u'nonce'] = random.randint(0, 10000000000000000000000000000000000000000)
    while det_hash(a) > custom.buy_shares_target:
        block[u'nonce'] += 1
        a={u'nonce': block['nonce'], u'halfHash': h}
    return block
def make_half_way(block):
    a = copy.deepcopy(block)
    a.pop('nonce')
    return({u'nonce': block['nonce'], u'halfHash': det_hash(a)})
def base58_encode(num):
    num = int(num, 16)
    alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    base_count = len(alphabet)
    encode = ''
    if num < 0:
        return ''
    while (num >= base_count):
        mod = num % base_count
        encode = alphabet[mod] + encode
        num = num / base_count
    if num:
        encode = alphabet[num] + encode
    return encode
def make_address(pubkeys, n):
    """n is the number of pubkeys required to spend from this address."""
    return (str(len(pubkeys)) + str(n) +
            base58_encode(det_hash({str(n): pubkeys}))[0:29])
def buffer_(str_to_pad, size):
    return str_to_pad.rjust(size, '0')
def E_check(dic, key, type_):
    if not isinstance(type_, list): type_=[type_]
    if len(type_)==0: return False#to end the recursion.
    if not key in dic: return False
    if isinstance(type_[0], type):
        if not isinstance(dic[key], type_[0]): return E_check(dic, key, type_[1:])
    else:
        if not dic[key] == type_[0]: return E_check(dic, key, type_[1:])
    return True
def is_number(s):
    try:
        int(s)
        return True
    except:
        return False
def kill_processes_using_ports(ports):
    popen = subprocess.Popen(['netstat', '-lpn'],
                             shell=False,
                             stdout=subprocess.PIPE)
    (data, err) = popen.communicate()
    pattern = "^tcp.*((?:{0})).* (?P<pid>[0-9]*)/.*$"
    pattern = pattern.format(')|(?:'.join(ports))
    prog = re.compile(pattern)
    for line in data.split('\n'):
        match = re.match(prog, line)
        if match:
            pid = match.group('pid')
            subprocess.Popen(['kill', '-9', pid])
def s_to_db(c): 
    response=networking.send_command(['localhost', custom.database_port], c)
    if (type(response)==dict and 'error' in response):
        time.sleep(0.001)
        log('s to db failed at '+str(c))
        log('s to db failed at '+str(response))
        #return s_to_db(c)
    else:
        return response
def local_get(k): return s_to_db({'type':'local_get', 'args':[str(k)]})
def local_put(k, v): return s_to_db({'type':'local_put', 'args':[str(k), v]})
def db_get(n, DB={}): return s_to_db({'type':'get', 'args':[str(n)]})
def db_put(key, dic, DB={}): return s_to_db({'type':'put', 'args':[str(key), dic]})
def db_delete(key, DB={}): return s_to_db({'type':'delete', 'args':[str(key)]})
def db_existence(key, DB={}): return s_to_db({'type':'existence', 'args':[str(key)]})
def db_proof(key): return s_to_db({'type':'proof', 'args':[str(key)]})
def db_verify(root, key, proof): return s_to_db({'type':'verify', 'args':[root, key, proof]})
def db_root(): return s_to_db({'type':'root', 'args':[]})
def fork_check(newblocks, DB, length, block):
    recent_hash = det_hash(block)
    their_hashes = map(lambda x: x['prev'] if x['length']>0 else 0, newblocks)+[det_hash(newblocks[-1])]
    b=(recent_hash not in their_hashes) and length>newblocks[0]['length']-1 and length<newblocks[-1]['length']
    return b
if __name__ == "__main__":
    a=POW({'a':'b'})
    print(a)
    '''
    time_0=time.time()
    for i in range(100):
        timea=time.time()
        POW({'empty':0})
        print(time.time()-timea)
    print(time.time()-time_0)
    '''

