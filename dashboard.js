const express = require("express");
const router = express.Router();

// Do we need to have this router use if we already have an app use in server js? look it up later
router.use(express.static(path.join(__dirname, "public")));

// Need another (maybe) router.use that acts as middleware checking for login whenever a dashboard related route is called. If token route to desired get, if no token back to "/"

router.get("/dashboard", (req, res) => {});
