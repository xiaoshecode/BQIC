class Obj:
    def __init__(self, obj):
        if type(obj) == self.__class__:
            object.__setattr__(self, "_parent", obj)
        else:
            object.__setattr__(self, "_parent", None)
            if type(obj) == dict:
                for k, v in obj.items():
                    self[k] = v
            elif type(obj) in (tuple, list):
                for i in range(len(obj)):
                    self[i] = obj[i]

    def __getitem__(self, item):
        return self.__dict__.get(
            item, None if self._parent == None else self._parent[item]
        )

    def __getattr__(self, item):
        return self[item]

    def __setitem__(self, item, val):
        self.__dict__[item] = val

    def __setattr__(self, item, val):
        self[item] = val

    def __repr__(self):
        return repr(self.__dict__)


class DDS:
    VERBOSE = True
    All = {}
    List = []
    Loc = {}

    def __init__(self, name, parent=None):
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_parent", parent)
        if parent == None:
            DDS.All[name] = self
            object.__setattr__(self, "_", Obj([0, 0, 0]))
        else:
            object.__setattr__(self, "_", Obj(parent._))

    def __getitem__(self, item):
        if type(item) == int or (item in ("f", "a", "p")):
            return self._[item]
        elif type(item) == str:
            r = self.__dict__.get(item, None)
            if r == None:
                r = self.__class__(item, self)
                r[0] = self[0]
                self.__dict__[item] = r
            return r

    def __getattr__(self, item):
        return self[item]

    def __setitem__(self, item, val):
        if type(item) == int or (item in ("f", "a", "p")):
            self._[item] = val
        elif type(item) == str:
            self.__dict__[item] = val

    def __setattr__(self, item, val):
        self[item] = val

    @property
    def name(self):
        name = []
        node = self
        while node != None:
            name.append(node._name)
            node = node._parent
        name.reverse()
        return name

    def __repr__(self):
        return ".".join(self.name) + (
            " = " + "[{}, {}, {}]".format(self[0], self[1], self[2])
            if DDS.VERBOSE
            else ""
        )

    def f(self, val=None, *args):
        if val == None:
            return self[0]
        else:
            self[0] = val
            return self

    def a(self, val=None, *args):
        if val == None:
            return self[1]
        else:
            self[1] = val
            return self

    def p(self, val=None, *args):
        if val == None:
            return self[2]
        else:
            self[2] = val
            return self

    def __call__(self, f=None, a=1, p=0):
        if f == None:
            return self[0], self[1], self[2]
        else:
            self[0], self[1], self[2] = f, a, p
            return self


class Seq:
    All = {}

    def __init__(self, name=""):
        Seq.All[name] = self
        self.seq = []

    def __repr__(self):
        # import json
        # return json.dumps(self.seq,default=lambda o:'.'.join(o.name),separators=(',',':'))
        return repr(self.seq)

    def __call__(self, *args):
        if len(args) == 0:
            self.seq.clear()
        else:
            self.seq.append(list(args))
        return self

    def __or__(self, rhs):
        if len(self.seq) == 0:
            self.seq.append([])
        self.seq[-1].append(rhs)
        return self

    def __getitem__(self, name):
        lhs = Seq.All.get(name, None)
        if lhs != None:

            def wrap(*rhs):
                if type(rhs) != tuple:
                    rhs = (rhs,)
                t = 0
                for i in range(len(lhs.seq)): # 遍历源序列的每个元素
                    d = rhs[i] # 获取对应的持续时间
                    s = []
                    for j in lhs.seq[i][:-1]:
                        if type(j) == DDS:
                            dds = j[str(i)]
                            mod = False
                            for k in range(3):
                                if type(j[k]) in (tuple, list): # 如果参数是序列
                                    dds[k] = j[k][i]
                                    mod = True
                                elif callable(j[k]): # 如果参数是可调用对象
                                    dds[k] = j[k](i, d, t) # 调用函数获取值
                                    mod = True
                            s.append(dds if mod else j)
                        else:
                            s.append(j)
                    # 序列更新
                    s.append(d )    # 添加持续时间
                    t += d # 累加持续时间
                    self.seq.append(s) # 将更新后的序列添加到当前序列中
                return self

            return wrap

    def __getattr__(self, name):
        return self[name]

    def __enter__(self):
        def add(lhs, rhs):
            return self(lhs, rhs)

        DDS.__or__ = add

    def __exit__(self, exc_type, exc_val, exc_tb):
        del DDS.__or__

    def compile(self, npfl=None, times=[0.1, 0.1, 4]):
        # 初始化序列和状态跟踪
        seq = []
        last_state = {i: None for i in DDS.List}
        # 处理每一行序列
        for row in self.seq:
            dur = row[-1] # 获取持续时间
            dds = row[:-1] # 获取DDS操作列表
            ttl = 0 # TTL 触发信号

            if len(dds) > 0 and type(dds[-1]) == int:
                ttl = dds[-1]
                dds = dds[:-1]
            # 构建当前状态
            state = {i: DDS.All[i].off for i in DDS.List}
            for i in dds:
                if type(i) == DDS:
                    state[i.name[0]] = i
            seq.append(
                [state[i] for i in DDS.List if state[i] != last_state[i]] + [ttl, dur]
            )
            last_state = state
        # 生成配置文件
        if npfl == None:
            # import json
            # seq = json.dumps(seq,default=lambda o:'.'.join(o.name),separators=(',',':'))
            return seq
        pfls = [[None] * npfl for i in range(len(DDS.List))]
        cseq = []
        write = []
        for i in seq[0][:-2]:
            loc = DDS.Loc[i.name[0]]
            write.append((loc, 0, i))
            pfls[loc][0] = i
        cseq.append(({}, 0, write, 0))
        # 处理时序
        for i in range(len(seq)):
            dur = seq[i][-1]
            change = {}
            for j in seq[i][:-2]:
                loc = DDS.Loc[j.name[0]]
                change[loc] = pfls[loc].index(j)
                dur -= times[0]
            ttl = seq[i][-2]
            dur -= times[1]
            write = []
            for j in range(i + 1, len(seq)):
                if dur < times[2]:
                    break
                for k in seq[j][:-2]:
                    if dur < times[2]:
                        break
                    loc = DDS.Loc[k.name[0]]
                    if k not in pfls[loc]:
                        try:
                            m = pfls[loc].index(None)
                        except:
                            if j == i + 1:
                                for m in range(len(pfls[loc])):
                                    if m != change.get(loc, None):
                                        break
                            else:
                                continue
                        write.append((loc, m, k))
                        pfls[loc][m] = k
                        dur -= times[2]
            cseq.append([change, ttl, write, dur])
        # import json
        # cseq = json.dumps(cseq,separators=(',',':'))
        return cseq
