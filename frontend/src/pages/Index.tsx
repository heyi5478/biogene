import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useTransition,
} from 'react';
import { Search, Database, ArrowLeft, AlertCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { FilterPanel, QueryMode } from '@/components/FilterPanel';
import { PatientSummary } from '@/components/PatientSummary';
import { PatientList } from '@/components/PatientList';
import { PatientListPager } from '@/components/PatientListPager';
import { PatientActions } from '@/components/PatientActions';
import { SearchSummary } from '@/components/SearchSummary';
import { ResultModules } from '@/components/ResultModules';
import { ConditionResults } from '@/components/ConditionResults';
import { usePatients, useConditionPatients } from '@/hooks/queries/usePatients';
import { PATIENT_PAGE_SIZE } from '@/services/patients';
import { usePatient } from '@/hooks/queries/usePatient';
import { ModuleId, ConditionRow, ConditionLogic } from '@/types/medical';

const tabModuleMap: Record<string, ModuleId[]> = {
  all: [],
  basic: ['basic'],
  opd: ['opd'],
  lab: [
    'aa',
    'msms',
    'biomarker',
    'aadc',
    'ald',
    'mma',
    'mps2',
    'lsd',
    'enzyme',
    'gag',
  ],
  specimen: ['dnabank', 'outbank'],
  nbs: ['bd', 'cah', 'dmd', 'g6pd', 'smaScid'],
};

function DetailLoadingSkeleton() {
  return (
    <div className="space-y-2" data-testid="patient-detail-loading">
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

const Index = () => {
  // Non-urgent updates for heavy submit transitions.
  const [, startSearchTransition] = useTransition();

  // Mode
  const [queryMode, setQueryMode] = useState<QueryMode>('patient');

  // Patient query state
  const [searchQuery, setSearchQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [page, setPage] = useState(1);
  const [selectedModules, setSelectedModules] = useState<ModuleId[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(
    null,
  );
  const [activeTab, setActiveTab] = useState('all');

  // Condition query state
  const [conditions, setConditions] = useState<ConditionRow[]>([]);
  const [conditionLogic, setConditionLogic] = useState<ConditionLogic>('AND');
  const [conditionSubmitted, setConditionSubmitted] = useState(false);
  const [conditionPatientId, setConditionPatientId] = useState<string | null>(
    null,
  );

  // Server-driven patient search — runs only after the user submits a query.
  const patientsQuery = usePatients(submittedQuery, page);
  const patientsPage = submittedQuery ? patientsQuery.data : undefined;
  const results = patientsPage?.items ?? [];
  const total = patientsPage?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PATIENT_PAGE_SIZE));

  // Server-driven condition search — gated until the user submits.
  const conditionRequest = useMemo(
    () => ({ conditions, logic: conditionLogic }),
    [conditions, conditionLogic],
  );
  const conditionQuery = useConditionPatients(
    conditionRequest,
    conditionSubmitted && conditions.length > 0,
  );
  const conditionResults = conditionSubmitted
    ? (conditionQuery.data ?? [])
    : [];

  // Patient mode: auto-select when the text search resolves to exactly one
  // patient. Keyed on total (the full hit count), not the page length, and
  // guarded against keepPreviousData placeholder so a stale page from a
  // prior search cannot select the wrong patient.
  // Condition mode keeps its pre-change UX (always shows the matched-list
  // table first; user clicks 查看 to drill into a single patient).
  useEffect(() => {
    if (
      total === 1 &&
      !patientsQuery.isPlaceholderData &&
      selectedPatientId === null &&
      results.length === 1
    ) {
      setSelectedPatientId(results[0].patientId);
    }
  }, [total, patientsQuery.isPlaceholderData, results, selectedPatientId]);

  // Detail bundle for the currently selected patient (either mode).
  const detailId = selectedPatientId ?? conditionPatientId ?? undefined;
  const detailQuery = usePatient(detailId);
  const displayPatient = detailQuery.data ?? null;

  const isInitialLoading =
    (queryMode === 'patient' && submittedQuery && patientsQuery.isPending) ||
    (queryMode !== 'patient' &&
      conditionSubmitted &&
      conditions.length > 0 &&
      conditionQuery.isPending);
  const isError =
    (queryMode === 'patient' && patientsQuery.isError) ||
    (queryMode !== 'patient' && conditionQuery.isError);
  const error =
    (queryMode === 'patient' ? patientsQuery.error : conditionQuery.error) ??
    null;
  const errorMessage =
    error instanceof Error ? error.message : '發生未知錯誤，請稍後再試。';
  const refetch =
    queryMode === 'patient' ? patientsQuery.refetch : conditionQuery.refetch;

  const effectiveModules: ModuleId[] =
    activeTab !== 'all' ? tabModuleMap[activeTab] || [] : selectedModules;

  // Patient query handlers
  const handleSearch = useCallback(() => {
    startSearchTransition(() => {
      setSubmittedQuery(searchQuery);
      setSelectedPatientId(null);
      setPage(1);
    });
  }, [searchQuery]);

  const handleClearAll = useCallback(() => {
    setSearchQuery('');
    setSubmittedQuery('');
    setPage(1);
    setSelectedModules([]);
    setSelectedPatientId(null);
    setActiveTab('all');
  }, []);

  const handleRemoveModule = useCallback((id: ModuleId) => {
    setSelectedModules((prev) => prev.filter((m) => m !== id));
  }, []);

  const handleJumpTo = useCallback((moduleId: ModuleId) => {
    setActiveTab('all');
    setSelectedModules([moduleId]);
    setTimeout(() => {
      document
        .getElementById(`section-${moduleId}`)
        ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }, []);

  // Condition query handlers
  const handleConditionSearch = useCallback(() => {
    startSearchTransition(() => {
      setConditionSubmitted(true);
      setConditionPatientId(null);
    });
  }, []);

  const handleConditionClear = useCallback(() => {
    setConditions([]);
    setConditionSubmitted(false);
    setConditionPatientId(null);
  }, []);

  // Mode switch
  const handleModeChange = useCallback((mode: QueryMode) => {
    setQueryMode(mode);
    setConditionPatientId(null);
    setSelectedPatientId(null);
  }, []);

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="shrink-0 border-b border-border bg-card px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
            <Database className="h-4 w-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-base font-bold leading-tight text-foreground">
              基因醫學整合查詢中心
            </h1>
            <p className="text-[11px] text-muted-foreground">
              依病人姓名或病歷號查詢，或以條件篩選病人主檔、門診、檢驗與檢體資料
            </p>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel */}
        <FilterPanel
          queryMode={queryMode}
          onQueryModeChange={handleModeChange}
          searchQuery={searchQuery}
          onSearchQueryChange={setSearchQuery}
          onSearch={handleSearch}
          selectedModules={selectedModules}
          onModulesChange={setSelectedModules}
          onClearAll={handleClearAll}
          conditions={conditions}
          conditionLogic={conditionLogic}
          onConditionsChange={setConditions}
          onConditionLogicChange={setConditionLogic}
          onConditionSearch={handleConditionSearch}
          onConditionClear={handleConditionClear}
        />

        {/* Right Content */}
        <main className="thin-scrollbar flex-1 space-y-3 overflow-y-auto p-4">
          {isError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>無法載入患者資料</AlertTitle>
              <AlertDescription className="space-y-3">
                <p>{errorMessage}</p>
                <Button size="sm" variant="outline" onClick={() => refetch()}>
                  重試
                </Button>
              </AlertDescription>
            </Alert>
          )}
          {!isError && isInitialLoading && (
            <div className="space-y-2" data-testid="patients-loading">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}
          {!isError && !isInitialLoading && queryMode === 'patient' && (
            <>
              {/* Search Summary */}
              <SearchSummary
                query={submittedQuery}
                patientCount={total}
                selectedModules={selectedModules}
                onRemoveModule={handleRemoveModule}
                onClearAll={handleClearAll}
              />

              {/* Empty state */}
              {!submittedQuery && (
                <div className="flex h-[60vh] flex-col items-center justify-center text-center">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                    <Search className="h-7 w-7 text-muted-foreground" />
                  </div>
                  <h2 className="mb-1 text-lg font-semibold text-foreground">
                    開始查詢
                  </h2>
                  <p className="max-w-md text-sm text-muted-foreground">
                    請在左側輸入病人姓名或病歷號，並選擇需要查看的資料模組，即可開始查詢。
                  </p>
                  <p className="mt-3 text-xs text-muted-foreground">
                    提示：可使用左側「快捷查詢」按鈕快速選取常用模組組合，或切換至「條件查詢」以欄位條件篩選病人
                  </p>
                </div>
              )}

              {/* No results */}
              {submittedQuery && total === 0 && (
                <div className="flex h-[40vh] flex-col items-center justify-center text-center">
                  <h3 className="mb-1 text-base font-semibold text-foreground">
                    找不到符合條件的病人
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    請確認病人姓名或病歷號是否正確，或嘗試其他搜尋條件。
                  </p>
                </div>
              )}

              {/* Multiple patients */}
              {submittedQuery &&
                total > 1 &&
                selectedPatientId === null && (
                  <>
                    <PatientList
                      patients={results}
                      total={total}
                      onSelect={setSelectedPatientId}
                    />
                    {pageCount > 1 && (
                      <PatientListPager
                        page={page}
                        pageCount={pageCount}
                        onPageChange={setPage}
                      />
                    )}
                  </>
                )}

              {/* Single / selected patient */}
              {selectedPatientId !== null && (
                <>
                  {total > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedPatientId(null)}
                      className="mb-1 h-7 px-2 text-xs"
                    >
                      <ArrowLeft className="mr-1 h-3.5 w-3.5" />
                      返回病人名單
                    </Button>
                  )}
                  {detailQuery.isPending || !displayPatient ? (
                    <DetailLoadingSkeleton />
                  ) : (
                    <>
                      <PatientSummary
                        patient={displayPatient}
                        onJumpTo={handleJumpTo}
                      />
                      <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <div className="flex items-center justify-between gap-2">
                          <TabsList className="h-8">
                            <TabsTrigger value="all" className="h-7 text-xs">
                              全部
                            </TabsTrigger>
                            <TabsTrigger value="basic" className="h-7 text-xs">
                              基本資料
                            </TabsTrigger>
                            <TabsTrigger value="opd" className="h-7 text-xs">
                              門診
                            </TabsTrigger>
                            <TabsTrigger value="lab" className="h-7 text-xs">
                              檢驗
                            </TabsTrigger>
                            <TabsTrigger
                              value="specimen"
                              className="h-7 text-xs"
                            >
                              檢體
                            </TabsTrigger>
                            <TabsTrigger value="nbs" className="h-7 text-xs">
                              新生兒篩檢
                            </TabsTrigger>
                          </TabsList>
                          <PatientActions patient={displayPatient} />
                        </div>
                        <TabsContent value={activeTab} className="mt-3">
                          <ResultModules
                            patient={displayPatient}
                            activeModules={effectiveModules}
                          />
                        </TabsContent>
                      </Tabs>
                    </>
                  )}
                </>
              )}
            </>
          )}
          {!isError && !isInitialLoading && queryMode !== 'patient' && (
            /* Condition query mode */
            <>
              {!conditionSubmitted && conditionPatientId === null && (
                <div className="flex h-[60vh] flex-col items-center justify-center text-center">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                    <Search className="h-7 w-7 text-muted-foreground" />
                  </div>
                  <h2 className="mb-1 text-lg font-semibold text-foreground">
                    條件查詢
                  </h2>
                  <p className="max-w-md text-sm text-muted-foreground">
                    請在左側設定查詢條件（模組 + 欄位 + 運算子 +
                    值），或使用常用條件模板，即可篩選符合條件的病人。
                  </p>
                </div>
              )}

              {conditionSubmitted && conditionPatientId === null && (
                <ConditionResults
                  conditions={conditions}
                  logic={conditionLogic}
                  matchedPatients={conditionResults}
                  onSelectPatient={setConditionPatientId}
                />
              )}

              {conditionPatientId !== null && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setConditionPatientId(null)}
                    className="mb-1 h-7 px-2 text-xs"
                  >
                    <ArrowLeft className="mr-1 h-3.5 w-3.5" />
                    返回條件查詢結果
                  </Button>
                  {detailQuery.isPending || !displayPatient ? (
                    <DetailLoadingSkeleton />
                  ) : (
                    <>
                      <PatientSummary
                        patient={displayPatient}
                        onJumpTo={handleJumpTo}
                      />
                      <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <div className="flex items-center justify-between gap-2">
                          <TabsList className="h-8">
                            <TabsTrigger value="all" className="h-7 text-xs">
                              全部
                            </TabsTrigger>
                            <TabsTrigger value="basic" className="h-7 text-xs">
                              基本資料
                            </TabsTrigger>
                            <TabsTrigger value="opd" className="h-7 text-xs">
                              門診
                            </TabsTrigger>
                            <TabsTrigger value="lab" className="h-7 text-xs">
                              檢驗
                            </TabsTrigger>
                            <TabsTrigger
                              value="specimen"
                              className="h-7 text-xs"
                            >
                              檢體
                            </TabsTrigger>
                            <TabsTrigger value="nbs" className="h-7 text-xs">
                              新生兒篩檢
                            </TabsTrigger>
                          </TabsList>
                          <PatientActions patient={displayPatient} />
                        </div>
                        <TabsContent value={activeTab} className="mt-3">
                          <ResultModules
                            patient={displayPatient}
                            activeModules={effectiveModules}
                          />
                        </TabsContent>
                      </Tabs>
                    </>
                  )}
                </>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;
