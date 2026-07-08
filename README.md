# AI 投資研究 App MVP v0.3

目標：把 AI Infrastructure 新聞整理成可追蹤的 Signal、Theme 與 Portfolio 建議。

## 啟動方式

```bash
cd ~/Downloads/ai_investment_app_mvp
pip3 install -r requirements.txt
streamlit run app.py
```

瀏覽器開啟：

```text
http://localhost:8501
```

## v0.3 更新

- 中文介面
- Dashboard 顯示主題名稱，不只顯示 T001 / T002
- 新增「今日動作」區塊
- 主題排名新增趨勢欄位
- 修正 Streamlit `use_container_width` 警告

## MVP 規則

- Score = Impact × Confidence
- Score >= 15：檢查部位
- Score 6–14：更新主題
- Score < 6：忽略

目前不會自動下單，只做研究與回測。
