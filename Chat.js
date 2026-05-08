import express from "express";
import mysql from "mysql2/promise";
import { GoogleGenerativeAI } from "@google/generative-ai";
import nodemailer from "nodemailer";
import * as cheerio from "cheerio";

const app = express();
app.use(express.json());

// ── CONFIG ─────────────────────────────────────────
const DB_CONFIG = {
  host: "localhost",
  port: 4306,
  user: "root",
  password: "",
  database: "keryar",
};

const GEMINI_API_KEY = ""; // 🔴 ADD YOUR KEY HERE

const KERYAR_PHONE = "+91 99132 62167";
const KERYAR_EMAIL = "connect@keryar.com";

// ── DB ─────────────────────────────────────────────
async function dbQuery(sql, params = []) {
  try {
    const db = await mysql.createConnection(DB_CONFIG);
    const [rows] = await db.execute(sql, params);
    await db.end();
    return rows;
  } catch (e) {
    console.error("DB error:", e.message);
    return null;
  }
}

// ── FAQ ────────────────────────────────────────────
async function searchFAQ(query) {
  const like = `%${query}%`;
  return await dbQuery(
    `SELECT question, answer FROM chatbot_faq
     WHERE status=1 AND (question LIKE ? OR answer LIKE ?)
     LIMIT 5`,
    [like, like]
  );
}

// ── AI ─────────────────────────────────────────────
async function getAIResponse(message) {
  if (!GEMINI_API_KEY) {
    return `Call us at ${KERYAR_PHONE}`;
  }

  try {
    const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const result = await model.generateContent(message);
    return result.response.text();

  } catch (e) {
    console.error("AI error:", e.message);
    return "Something went wrong with AI.";
  }
}

// ── ROUTES ─────────────────────────────────────────

// Main chatbot endpoint
app.post("/chat", async (req, res) => {
  const { action, message } = req.body;

  try {
    if (action === "chat") {

      // 1. Check FAQ first
      const faq = await searchFAQ(message);

      if (faq && faq.length > 0) {
        return res.json({
          text: faq[0].answer
        });
      }

      // 2. Otherwise AI
      const aiReply = await getAIResponse(message);

      return res.json({
        text: aiReply
      });
    }

    return res.status(400).json({ error: "Invalid action" });

  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "Server error" });
  }
});

// ── START SERVER ───────────────────────────────────
app.listen(3000, () => {
  console.log("🚀 Server running at http://localhost:3000");
});