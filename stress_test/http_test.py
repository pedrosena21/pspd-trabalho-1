import uuid
import random
from locust import HttpUser, task, between


def random_name():
    return f"player-{uuid.uuid4().hex[:8]}"


class BingoUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.game_id = None
        self.player_id = None
        self.last_drawn = None

        try:
            resp = self.client.post(
                "/game/create",
                json={"name": f"stress-game-{uuid.uuid4().hex[:6]}", "max_players": 100},
                name="POST /game/create",
                catch_response=True,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                self.game_id = data.get("game_id") or data.get("id")
            else:
                resp.failure(f"create failed: {resp.status_code}")
        except Exception:
            pass

        try:
            payload = {"player_name": random_name()}
            if self.game_id:
                payload["game_id"] = self.game_id
            resp = self.client.post(
                "/game/register",
                json=payload,
                name="POST /game/register",
                catch_response=True,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                self.player_id = data.get("player_id") or data.get("id")
                self.card = data.get("card")
            else:
                resp.failure(f"register failed: {resp.status_code}")
        except Exception:
            pass

    @task(2)
    def get_card(self):
        if not self.player_id:
            return
        params = {"player_id": self.player_id}
        if self.game_id:
            params["game_id"] = self.game_id
        with self.client.get(
            "/game/card", params=params, name="GET /game/card", catch_response=True
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"card failed: {resp.status_code}")
            else:
                try:
                    self.card = resp.json()
                except Exception:
                    pass

    @task(1)
    def draw_number(self):
        if not self.game_id:
            return
        with self.client.post(
            "/game/draw",
            json={"game_id": self.game_id},
            name="POST /game/draw",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201):
                try:
                    data = resp.json()
                    self.last_drawn = data.get("number") or data.get("drawn")
                except Exception:
                    pass
            else:
                resp.failure(f"draw failed: {resp.status_code}")

    @task(3)
    def mark_number(self):
        if not self.player_id:
            return
        number = self.last_drawn or random.randint(1, 75)
        payload = {"player_id": self.player_id, "number": number}
        if self.game_id:
            payload["game_id"] = self.game_id
        with self.client.post(
            "/game/mark", json=payload, name="POST /game/mark", catch_response=True
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"mark failed: {resp.status_code}")

    @task(1)
    def check_bingo(self):
        if not self.player_id:
            return
        payload = {"player_id": self.player_id}
        if self.game_id:
            payload["game_id"] = self.game_id
        with self.client.post(
            "/game/bingo", json=payload, name="POST /game/bingo", catch_response=True
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"bingo check failed: {resp.status_code}")


if __name__ == "__main__":
    import os
    host = os.environ.get("LOCUST_HOST", "http://bingo-api:80")
    os.system(f"locust -f stress_test/http_test.py --host={host}")