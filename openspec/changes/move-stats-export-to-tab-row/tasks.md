## 1. 建立 PatientActions 元件

- [x] 1.1 新增 `frontend/src/components/PatientActions.tsx`，export `PatientActions({ patient }: { patient: Patient })`
- [x] 1.2 在 `PatientActions` 內加入 `statsOpen` / `exportOpen` 兩個 `useState`
- [x] 1.3 渲染 `<div className="flex items-center gap-1 shrink-0">`，內含兩顆 Button：
  - 統計：`variant="success" size="sm" className="h-6 px-2 text-[10px]"`、icon `<BarChart3 className="mr-1 h-3 w-3" />`、`onClick={() => setStatsOpen(true)}`
  - 匯出：`variant="info" size="sm" className="h-6 px-2 text-[10px]"`、icon `<Download className="mr-1 h-3 w-3" />`、`onClick={() => setExportOpen(true)}`
- [x] 1.4 在同一元件尾端渲染 `<StatsDialog open={statsOpen} onOpenChange={setStatsOpen} patient={patient} />` 與 `<ExportDialog open={exportOpen} onOpenChange={setExportOpen} patient={patient} />`
- [x] 1.5 import 所需項目：`React`、`Button`、`BarChart3`、`Download`、`StatsDialog`、`ExportDialog`、`Patient`

## 2. 從 PatientSummary 移除統計／匯出相關程式碼

- [x] 2.1 從 `frontend/src/components/PatientSummary.tsx` 的 lucide-react import 移除 `BarChart3` 與 `Download`
- [x] 2.2 移除 `StatsDialog` 與 `ExportDialog` 的 import（來自 `@/components/stats/StatsDialog` 與 `@/components/export/ExportDialog`）
- [x] 2.3 移除 `const [statsOpen, setStatsOpen] = React.useState(false);` 與 `const [exportOpen, setExportOpen] = React.useState(false);`
- [x] 2.4 刪除「統計」按鈕 JSX（原第 145-153 行）
- [x] 2.5 刪除「匯出」按鈕 JSX（原第 154-162 行）
- [x] 2.6 刪除 `<Card>` 尾端的 `<StatsDialog ... />` 與 `<ExportDialog ... />` 兩個渲染（原第 179-188 行）
- [x] 2.7 確認保留：模組跳轉按鈕的 JSX 與外層 `<div className="flex max-w-[260px] flex-wrap justify-end gap-1">`、以及 `ageInYears` 的 import

## 3. 在 Tab 列渲染 PatientActions

- [x] 3.1 在 `frontend/src/pages/Index.tsx` 加入 `import { PatientActions } from '@/components/PatientActions';`
- [x] 3.2 把原本的 `<TabsList className="h-8">...</TabsList>` 改為包在一個 flex 容器中（同時套用至 patient 與 condition 查詢兩個 Tabs 區塊，以保留 condition 查詢中的統計／匯出入口）：
  ```tsx
  <div className="flex items-center justify-between gap-2">
    <TabsList className="h-8">{/* 6 個 TabsTrigger 保持不變 */}</TabsList>
    <PatientActions patient={displayPatient} />
  </div>
  ```
- [x] 3.3 確認 `<TabsContent>` 與其他 `<Tabs>` 內部結構不變、`activeTab` / `setActiveTab` 綁定不變

## 4. 驗證

- [x] 4.1 執行 `npm run -w frontend typecheck`（或 `tsc --noEmit`）確認無型別錯誤
- [x] 4.2 執行 lint（`npm run -w frontend lint` 或專案設定的指令）確認無 unused import 警告
- [ ] 4.3 啟動前端 dev server，搜尋一位病人（例如 `A1234567`），進入病人詳情頁
- [ ] 4.4 視覺驗證：`統計` 與 `匯出` 按鈕出現在 Tab 列右側；`PatientSummary` 右側僅剩模組跳轉按鈕
- [ ] 4.5 點擊 `統計` → `StatsDialog` 開啟且顯示該病人資料；關閉後重開正常
- [ ] 4.6 點擊 `匯出` → `ExportDialog` 開啟；關閉後重開正常
- [ ] 4.7 切換 Tab（全部 / 基本資料 / 門診 / 檢驗 / 檢體 / 新生兒篩檢）→ 切換正常、按鈕保持在右側
- [ ] 4.8 點擊 `PatientSummary` 裡的模組跳轉按鈕（例如 `門診 (3)`）→ Tab 與顯示模組正常連動
- [ ] 4.9 縮窄瀏覽器寬度至 1024px / 768px → Tab 列不破版、按鈕不被壓碎
- [x] 4.10 確認 `frontend/src/components/PatientSummary.tsx` 中仍無 `calcAge` 函式宣告（`grep -n "function calcAge\|const calcAge" frontend/src/components/PatientSummary.tsx` 應為空）

## 5. 文件與收尾

- [x] 5.1 執行 `openspec validate move-stats-export-to-tab-row --strict` 確認 change 驗證通過
- [x] 5.2 準備好 archive 所需資訊（實作完成後透過 `/opsx:archive` 收斂 specs）
