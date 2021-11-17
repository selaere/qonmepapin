import irc.client_aio
import irc.client
import asyncio
from fractions import Fraction
import re
import logging
import random
from typing import Callable, Awaitable

logging.basicConfig(level=logging.INFO)


Event = Callable[[
    irc.client_aio.AioConnection,  # conn
    irc.client.Event,              # event
], Awaitable[None]]

events: dict[str, Event] = {}

def event(func: Event) -> None:
    events[func.__name__] = func
    logging.info(f"event {func.__name__} added.")


Command = Callable[[
    irc.client_aio.AioConnection,  # conn
    irc.client.Event,              # event
    str,                           # args
    Callable[[str], None],         # send
], Awaitable[None]]

commands: dict[str, Command] = {}

def command(*names: str) -> Callable[[Command], None]:
    def pred(command_func: Command):
        for name in names:
            commands[name] = command_func
            logging.info(f"command {name} added.")

    return pred


server, port, nickname, channels = "irc.osmarks.net", 6667, "qonmepapin", ["#aa", "#b"]


@event
async def on_welcome(conn, event):
    print("!!!")
    for chan in channels:
        conn.join(chan)


@event
async def on_join(conn, event):
    logging.info("joined " + event.target)


@event
async def on_pubmsg(conn, event):
    def send(message):
        conn.privmsg(event.target, message)
    msg = event.arguments[0]
    if (match := re.search(r"\bq(?:onmepapi|8)n,? ", msg)):
        cmdname, _, args = msg[match.end(0):].partition(" ")
        if (cmd := commands.get(cmdname)):
            try:
                await cmd(conn, event, args, send)
            except Exception as e:
                send("a \x034\x02FATAL ERROR\x0F occured!!!!! fear.")
                logging.error(e)
        else:
            send(f"{nickname} cannot {cmdname}.")

@command("say")
async def cmd_say(conn, event, args, send):
    send(args)

@command("add", "sum")
async def cmd_sum(conn, event, args, send):
    send(str(sum(Fraction(i) for i in args.split(" "))))

@command("die")
async def cmd_die(conn, event, args, send):
    send("dying...")
    conn.quit("dead")
    quit()

@command("sudo")
async def cmd_sudo(conn, event, args, send):
    send(f"{event.source.nick} is not in the sudoers file.   This incident will be reported.")

@command("dont", "don't")
async def cmd_dont(conn, event, args, send):
    verb, sep, obj = args.partition(" ")
    if verb == "do": verb = "doe"
    if verb.endswith("y"): verb = verb[:-1] + "ie"
    send(f"*{verb}s{sep}{obj}*".strip())

@command("ping")
async def cmd_ping(conn, event, args, send):
    send("pong")

@command("pong")
async def cmd_pong(conn, event, args, send):
    send("ping")

@command("bee")
async def cmd_bee(conn, event, args, send):

    def randnum() -> int:
        return 1 + int(1 / random.random())

    sus = [
        lambda: "bee" + "e" * randnum() + random.choice(["", "", "s"]) + "!" * randnum(),
        lambda: "bee" + "e" * randnum() + random.choice(["", "", "s"]) + "!" * randnum(),
        lambda: "bee" + "e" * randnum() + random.choice(["", "", "s"]) + "!" * randnum(),
        lambda: "bz" + "z" * randnum() + random.choice(["t", ""]),
        lambda: "bz" + "z" * randnum() + random.choice(["t", ""]),
        lambda: "bz" + "z" * randnum() + random.choice(["t", ""]),
        lambda: "c:",
        lambda: "apio",
        lambda: (
            random.choice(["y", "Y"])
            + ''.join(random.choice(["y", "Y", "a", "A"]) for _ in range(randnum())))
    ]
    length = (50 + random.random() * 200)
    msg = random.choice(sus)()
    while len(msg) + len(newword := (random.choice(sus)())) < length:
        msg += newword if random.random() < 0.7 else newword.upper()
        if random.random() < 0.7: msg += " "
    send(msg.replace("  ", " ").strip())


@command("can")
async def cmd_can(conn, event, args, send):
    if args:
        cmdname, _, _ = args.partition(" ")
    else:
        cmdname = random.choice(list(commands.keys()))
    send(f"{nickname} can{'not' if cmdname not in commands else ''} {cmdname}.")


def main():

    def dispatcher(conn, event):
        if (func := events.get("on_" + event.type)):
            asyncio.create_task(func(conn, event))

    reactor = irc.client_aio.AioReactor()
    reactor.add_global_handler("all_events", dispatcher, -10)

    reactor.loop.run_until_complete(
        reactor.server().connect(server, port, nickname))
    print("bees")
    reactor.process_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("ok :)")
