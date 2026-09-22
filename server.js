require("dotenv").config();

const path = require("path");
const https = require("https");
const fs = require("fs");
const crypto = require("node:crypto");
const session = require("express-session");

const PORT = process.env.PORT;
const SESSION_SECRET = process.env.SESSION_SECRET;
const API_KEY = process.env.api_key;
const CLIENT_ID = process.env.oauth_client_id;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URL = process.env.redirect_uri;
const ENCODED_REDIRECT = encodeURIComponent(REDIRECT_URL);

const express = require("express");
const app = express();

app.use(
  session({
    secret: SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: true,
    },
  }),
);

// Serve files from the 'public' directory. Serving means they are accesible via URL
app.use(express.static(path.join(__dirname, "public")));

// Login Route
app.get("/login", (req, res) => {
  // Generate a random 16-byte 'state' value
  const state = crypto.randomBytes(16);

  // Convert the state to different string types:
  const stateStr = state.toString("hex");

  // Set sessoin's state var to our per-login random value generated above
  req.session.oauthState = stateStr;

  // Build link with required parameters
  res.redirect(
    `https://www.bungie.net/en/oauth/authorize?state=${stateStr}&client_id=${CLIENT_ID}&response_type=code&redirect_uri=${ENCODED_REDIRECT}`,
  );
});

// Callback Route
// We need to catch code and state from the callback response. Check state against our local one to ensure they match.
// if they dont we reject. if they do we use a POST and the code object to get a token from bungie
app.get("/callback", async (req, res) => {
  if (req.query.state != req.session.oauthState) {
    res.status(400).send("Error: State Mismatch");
  } else {
    const params = new URLSearchParams({
      grant_type: "authorization_code",
      code: req.query.code,
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
    });

    // States match; use code object to get a token from bungie
    const response = await fetch(
      "https://www.bungie.net/platform/app/oauth/token/",
      {
        method: "POST",
        headers: {
          "X-API-Key": API_KEY,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params,
      },
    );

    req.session.tokenData = await response.json();
    res.redirect("dashboard");
  }
});

// 1. Read your SSL certificate and key files
const options = {
  key: fs.readFileSync(path.join(__dirname, "127.0.0.1-key.pem")),
  cert: fs.readFileSync(path.join(__dirname, "127.0.0.1.pem")),
};

const server = https.createServer(options, app);

server.listen(PORT, () => {
  console.log(`HTTPS Server running on port https://127.0.0.1:${PORT}`);
});
