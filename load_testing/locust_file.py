from locust import HttpUser, task


class MyUser(HttpUser):
    @task(5)
    def get_items(self):
        response = self.client.get('/items')
        print(response.text)

        if response.status_code != 200: return

        data = response.json()

        for item in data:
            id = item['id']
            # print(id)
            self.client.get(f'/items/{id}')

    @task
    def get_locations(self):
        self.client.get('/location')
