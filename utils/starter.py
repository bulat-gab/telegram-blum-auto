from asyncio import sleep
from random import uniform

import aiohttp
from aiocfscrape import CloudflareScraper
from .agents import generate_random_user_agent

from data import config
from utils.blum import BlumBot
from utils.core import logger
from utils.helper import format_duration


async def start(thread: int, account: str, proxy: [str, None]):
    while True:
        async with CloudflareScraper(headers={'User-Agent': generate_random_user_agent(device_type='android',
                                                                                       browser_type='chrome')},
                                     timeout=aiohttp.ClientTimeout(total=60)) as session:
            try:
                blum = BlumBot(account=account, thread=thread, session=session, proxy=proxy)
                max_try = 2

                await sleep(uniform(*config.DELAYS['ACCOUNT']))
                await blum.login()

                while True:
                    try:
                        if config.SOLVE_TASKS:
                            async def solve_task(t):
                                task_status = t.get('status')
                                if task_status == "READY_FOR_CLAIM":
                                    task_claimed = await blum.claim_task(t)
                                    if task_claimed:
                                        logger.success(f"{account} | Claimed task id '{t['id']}' title: '{t['title']}'")
                                    else:
                                        logger.warning(f"{account} | Could not claim task. task id: {t['id']}; title: {t['title']}")


                                elif task_status == "NOT_STARTED":
                                    task_started = await blum.start_complete_task(t)
                                    if task_started:
                                        logger.info(f"{account} | Started task id '{t['id']}' title: '{t['title']}'")
                                    else:
                                        logger.warning(f"{account} | Could not start task. task id: {t['id']}; title: {t['title']}")

                                elif task_status == "STARTED":
                                    logger.info(f"{account} | Task started but cannot be claimed yet. task id: {t['id']}; title: {t['title']}")

                                else:
                                    logger.warning(f"{account} | Unknown task status: {task_status}. task id '{t['id']}' title: '{t['title']}'")
                                
                            try:
                                tasks = await blum.get_tasks()
                                tasks = [t for t in tasks if t.get('status') != "FINISHED" and t.get('status') != "ONGOING"]
                                logger.info(f"{account} | Tasks available: {len(tasks)}")

                                for t in tasks:
                                    task_kind = t.get('kind')
                                    if task_kind == "INITIAL":
                                        await solve_task(t)
                                    
                                    elif task_kind == "QUEST":
                                        sub_tasks = t.get('subTasks')
                                        logger.info(f"{account} | Task '{t['id']}' contains {len(sub_tasks)} sub tasks")
                                        for sub_task in sub_tasks:
                                            await solve_task(sub_task)
                                            await sleep(uniform(3, 10))
                                    elif task_kind == "ONGOING":
                                        # TODO: Handle Ongoing tasks (Example: Farming 10000 Blum points)
                                        continue

                                    await sleep(uniform(3, 10))


                            except Exception as e:
                                logger.error(f"{account} | Error during task claiming: {e}")
      

                        msg = await blum.claim_daily_reward()
                        if isinstance(msg, bool) and msg:
                            logger.success(f"{account} | Claimed daily reward!")

                        timestamp, start_time, end_time, play_passes = await blum.balance()

                        claim_amount, is_available = await blum.friend_balance()
                        logger.info(f"{account} | {claim_amount} | {is_available}")
                        if claim_amount != 0 and is_available:
                            amount = await blum.friend_claim()
                            logger.success(f"{account} | Claimed friend ref reward {amount}")

                        if config.PLAY_GAMES is False:
                            play_passes = 0
                        elif play_passes and play_passes > 0 and config.PLAY_GAMES is True:
                            await blum.play_game(play_passes)

                        await sleep(uniform(3, 10))

                        try:
                            timestamp, start_time, end_time, play_passes = await blum.balance()
                            if start_time is None and end_time is None and max_try > 0:
                                await blum.start()
                                logger.info(f"{account} | Start farming!")
                                max_try -= 1

                            elif (start_time is not None and end_time is not None and timestamp is not None and 
                                  timestamp >= end_time and max_try > 0):
                                await blum.refresh()
                                timestamp, balance = await blum.claim()
                                logger.success(f"{account} | Claimed reward! Balance: {balance}")
                                max_try -= 1

                            elif end_time is not None and timestamp is not None:
                                sleep_duration = end_time - timestamp
                                logger.info(f"{account} | Sleep {format_duration(sleep_duration)}")
                                max_try += 1
                                await sleep(sleep_duration)
                                await blum.refresh()

                            elif max_try == 0:
                                break

                        except Exception as e:
                            logger.error(f"{account} | Error in farming management: {e}")

                        await sleep(10)
                    except Exception as e:
                        logger.error(f"{account} | Error: {e}")
            except Exception as outer_e:
                logger.error(f"{account} | Session error: {outer_e}")
            finally:
                logger.info(f"{account} | Reconnecting, 61 s")
                await sleep(61)


async def stats():
    logger.success("Analytics disabled")
