"use client";

import React from "react";
import styles from "./page.module.css";

export default function Home() {
    React.useEffect(() => {
    // Ajoute data-tag à chaque élément HTML
    const all = document.querySelectorAll("*");
    all.forEach((el) => {
      if (el instanceof HTMLElement && !el.hasAttribute("data-tag")) {
        el.setAttribute("data-tag", el.tagName.toLowerCase());
      }
    });
  }, []);
  return (
    <h1>Work in progress</h1>
  );
}
