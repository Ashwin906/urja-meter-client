import httpx


class UrjaPortalClient:
    BASE_URL = "https://urja-ops.flockenergy.tech"

    def __init__(self, email: str, password: str):
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=20.0,
            follow_redirects=True,
        )
        self.login(email, password)

    def login(self, email: str, password: str):
        # Establish the initial session.
        self.client.get("/login").raise_for_status()

        headers = {
            "Origin": self.BASE_URL,
            "Referer": f"{self.BASE_URL}/login",
            "x-sveltekit-action": "true",
        }

        response = self.client.post(
            "/login",
            data={
                "email": email,
                "password": password,
            },
            headers=headers,
        )
        response.raise_for_status()

        result = response.json()

        if result.get("type") != "redirect":
            raise RuntimeError("Portal login did not return the expected response")

        if not self.client.cookies:
            raise RuntimeError("Login succeeded without a session cookie")

    def get_meter_page(self, query="", page=1):
        response = self.client.get(
            "/portal/meters/search",
            params={"q": query, "page": page},
        )
        response.raise_for_status()

        result = response.json()

        required_fields = {"data", "total", "page", "pageSize"}
        if not required_fields.issubset(result):
            raise ValueError("Unexpected meter-search response format")

        if not isinstance(result["data"], list):
            raise ValueError("'data' must be a list")

        return result

    def get_all_meters(self, query="", max_pages=100):
        first_page = self.get_meter_page(query=query, page=1)

        total = first_page["total"]
        page_size = first_page["pageSize"]

        if not isinstance(total, int) or total < 0:
            raise ValueError("Invalid total count")

        if not isinstance(page_size, int) or page_size <= 0:
            raise ValueError("Invalid page size")

        total_pages = (total + page_size - 1) // page_size

        if total_pages > max_pages:
            raise ValueError(
                f"Dataset requires {total_pages} pages; "
                f"maximum allowed is {max_pages}"
            )

        meters = list(first_page["data"])

        for page in range(2, total_pages + 1):
            result = self.get_meter_page(query=query, page=page)

            if result["total"] != total:
                raise RuntimeError("Total record count changed during extraction")

            if result["pageSize"] != page_size:
                raise RuntimeError("Page size changed during extraction")

            meters.extend(result["data"])

        if len(meters) != total:
            raise RuntimeError(
                f"Incomplete extraction: expected {total}, received {len(meters)}"
            )

        return meters

    def get_meter_details(self, meter_id: str):
        response = self.client.get(f"/meters/{meter_id}")
        response.raise_for_status()
        return response

    def get_meter_geo(self, meter_id: str):
        response = self.client.get(
            f"/portal/meters/{meter_id}/geo"
        )
        response.raise_for_status()

        result = response.json()

        if "data" not in result:
            raise ValueError("Unexpected geography response format")

        return result


    def get_meter_energy(self, meter_id: str):
        response = self.client.get(
            f"/portal/meters/{meter_id}/energy"
        )
        response.raise_for_status()

        result = response.json()

        if "data" not in result or not isinstance(result["data"], list):
            raise ValueError("Unexpected energy response format")

        return result

    def get_transformer_page(self, page=1):
        response = self.client.get(
            "/portal/dts",
            params={"page": page},
        )
        response.raise_for_status()
    
        result = response.json()
    
        if "data" not in result or not isinstance(result["data"], list):
            raise ValueError("Unexpected transformer response format")
    
        return result

    def get_all_transformers(self, max_pages=100):
        
        first_page = self.get_transformer_page(page=1)

        total = first_page["total"]
        page_size = first_page["pageSize"]

        if not isinstance(total, int) or total < 0:
            raise ValueError("Invalid transformer total count")

        if not isinstance(page_size, int) or page_size <= 0:
            raise ValueError("Invalid transformer page size")

        total_pages = (total + page_size - 1) // page_size

        if total_pages > max_pages:
            raise ValueError(
                f"Transformer extraction requires {total_pages} pages; "
                f"maximum allowed is {max_pages}"
            )

        transformers = list(first_page["data"])

        for page in range(2, total_pages + 1):
            result = self.get_transformer_page(page=page)

            if result["total"] != total:
                raise RuntimeError(
                    "Transformer total changed during extraction"
                )

            if result["pageSize"] != page_size:
                raise RuntimeError(
                    "Transformer page size changed during extraction"
                )

            transformers.extend(result["data"])

        if len(transformers) != total:
            raise RuntimeError(
                f"Incomplete extraction: expected {total} transformers, "
                f"received {len(transformers)}"
            )

        return transformers

    def close(self):
        self.client.close()