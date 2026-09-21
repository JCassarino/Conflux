require("dotenv").config();

const path = require("path");
const PORT = process.env.PORT;
const API_KEY = process.env.api_key;
const CLIENT_ID = process.env.oauth_client_id;
const REDIRECT_URL = process.env.redirect_uri;

const express = require("express");
const app = express();

// Serve files from the 'public' directory. Serving means they are accesible via URL
app.use(express.static(path.join(__dirname, "public")));

app.get("/login", (req, res) => {
  const bungieAuthURL = `https://bungie.net{CLIENT_ID}&response_type=code`;
  res.redirect(bungieAuthUrl);
});

app.listen(PORT, "127.0.0.1", () => {
  console.log(`Server is running at http://127.0.0.1:${PORT}`);
});
