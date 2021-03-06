# -*- coding: utf-8 -*-

import os
import asyncio
import aiotarantool
import string
import multiprocessing


class Bench(object):
    def __init__(self, aiotnt):
        self.tnt = aiotnt
        self.mod_len = len(string.printable)
        self.data = [string.printable[it] * 1536 for it in range(self.mod_len)]

        self.cnt_i = 0
        self.cnt_s = 0
        self.cnt_u = 0
        self.cnt_d = 0

        self.iter_max = 10000

    async def insert_job(self):
        for it in range(self.iter_max):
            try:
                await self.tnt.insert("tester", (it, self.data[it % self.mod_len]))
                self.cnt_i += 1
            except self.tnt.DatabaseError:
                pass

    async def select_job(self):
        for it in range(self.iter_max):
            rs = await self.tnt.select("tester", it)
            if len(rs):
                self.cnt_s += 1

    async def update_job(self):
        for it in range(self.iter_max):
            try:
                await self.tnt.update("tester", it, [("=", 2, it)])
                self.cnt_u += 1
            except self.tnt.DatabaseError:
                pass

    async def delete_job(self):
        for it in range(0, self.iter_max, 2):
            rs = await self.tnt.delete("tester", it)
            if len(rs):
                self.cnt_d += 1


def target_bench(loop):
    print("run process:", os.getpid())
    tnt = aiotarantool.connect("127.0.0.1", 3301)
    bench = Bench(tnt)

    tasks = []
    tasks += [loop.create_task(bench.insert_job())
              for _ in range(20)]

    tasks += [loop.create_task(bench.select_job())
              for _ in range(20)]

    tasks += [loop.create_task(bench.update_job())
              for _ in range(20)]

    tasks += [loop.create_task(bench.delete_job())
              for _ in range(20)]

    t1 = loop.time()
    loop.run_until_complete(asyncio.wait(tasks))
    t2 = loop.time()

    loop.run_until_complete(tnt.close())

    print("select=%d; insert=%d; update=%d; delete=%d; total=%d" % (
        bench.cnt_s, bench.cnt_i, bench.cnt_u, bench.cnt_d, t2 - t1))

    loop.close()


loop = asyncio.get_event_loop()

workers = [multiprocessing.Process(target=target_bench, args=(loop,))
           for _ in range(22)]

for worker in workers:
    worker.start()

for worker in workers:
    worker.join()
