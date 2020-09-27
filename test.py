import asyncio
import socket
import time


async def test1():
    print('test1')
    await asyncio.sleep(3)
    print('end1')


async def test2():
    print('test2')
    time.sleep(4)
    print('end2')



loop = asyncio.get_event_loop()
loop.create_task(test1())
loop.create_task(test2())
loop.run_forever()