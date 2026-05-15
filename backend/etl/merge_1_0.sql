-- merge_1_0.sql — merge the 1.0 dataset (restored into v10_* schemas) into
-- the live 2.0 canonical. Method 2: keep the 2.0 row on overlap and
-- back-fill only its empty/NULL columns from 1.0; insert 1.0-unique rows
-- fresh. One transaction — any error rolls the whole merge back.
-- Re-runnable: 4b clears prior 1.0-merge rows so 4c-4e re-apply cleanly.
-- See backend/etl/LOAD_2_0_PROD.md §1.0 merge runbook.
\set ON_ERROR_STOP on
BEGIN;

\echo '=== 1.0 -> canonical merge (method 2) — commits on success ==='

-- 4a. patient merge (column list built per schema — main.patient has
--     referring_doctor, external/nbs do not)
DO $$
DECLARE s text; cols text; setlist text; n bigint; before_n bigint; after_n bigint;
BEGIN
  FOREACH s IN ARRAY ARRAY['main','external','nbs'] LOOP
    SELECT string_agg(quote_ident(column_name), ', ' ORDER BY ordinal_position)
      INTO cols
    FROM information_schema.columns
    WHERE table_schema = s AND table_name = 'patient';
    SELECT string_agg(format('%1$I = COALESCE(p.%1$I, EXCLUDED.%1$I)', column_name), ', ')
      INTO setlist
    FROM information_schema.columns
    WHERE table_schema = s AND table_name = 'patient' AND column_name <> 'patient_id';
    EXECUTE format('SELECT count(*) FROM %I.patient', s) INTO before_n;
    EXECUTE format(
      'INSERT INTO %1$I.patient AS p (%2$s) SELECT %2$s FROM v10_%1$I.patient '
      'ON CONFLICT (patient_id) DO UPDATE SET %3$s',
      s, cols, setlist);
    GET DIAGNOSTICS n = ROW_COUNT;
    EXECUTE format('SELECT count(*) FROM %I.patient', s) INTO after_n;
    RAISE NOTICE '4a patient %  : touched=%  count % -> %  (new=%)',
      rpad(s,8), n, before_n, after_n, after_n - before_n;
  END LOOP;
END $$;

-- 4b. idempotency reset
DO $$
DECLARE r record; n bigint; tot bigint := 0;
BEGIN
  FOR r IN SELECT table_name, substring(table_schema FROM 5) AS live
           FROM information_schema.tables
           WHERE table_schema IN ('v10_main','v10_external','v10_nbs')
             AND table_type='BASE TABLE' AND table_name<>'patient'
  LOOP
    EXECUTE format('DELETE FROM %I.%I WHERE v2_source_schema = ''1.0-mdb''',
                   r.live, r.table_name);
    GET DIAGNOSTICS n = ROW_COUNT; tot := tot + n;
  END LOOP;
  RAISE NOTICE '4b idempotency reset : % prior 1.0-merge rows cleared', tot;
END $$;

-- 4c. overlap back-fill
DO $$
DECLARE r record; setlist text; n bigint;
BEGIN
  FOR r IN
    SELECT t.table_name, substring(t.table_schema FROM 5) AS live
    FROM information_schema.tables t
    WHERE t.table_schema IN ('v10_main','v10_external','v10_nbs')
      AND t.table_type='BASE TABLE' AND t.table_name<>'patient'
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                  WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name
                    AND c.column_name='patient_id')
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                  WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name
                    AND c.column_name='ntubiogene_sampleno')
  LOOP
    SELECT string_agg(
             format('%1$I = COALESCE(%2$s, v.%1$I)', column_name,
                    CASE WHEN data_type IN ('character varying','text','character')
                         THEN format('NULLIF(b.%I, '''')', column_name)
                         ELSE format('b.%I', column_name) END), ', ')
      INTO setlist
    FROM information_schema.columns
    WHERE table_schema='v10_'||r.live AND table_name=r.table_name
      AND is_identity='NO' AND column_name NOT IN ('patient_id','ntubiogene_sampleno');
    EXECUTE format(
      'UPDATE %1$I.%2$I b SET %3$s FROM v10_%1$I.%2$I v '
      'WHERE b.patient_id=v.patient_id AND b.ntubiogene_sampleno=v.ntubiogene_sampleno',
      r.live, r.table_name, setlist);
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n > 0 THEN
      RAISE NOTICE '4c back-fill %.%  : % rows updated', r.live, r.table_name, n;
    END IF;
  END LOOP;
END $$;

-- 4d. 1.0-unique inserts
DO $$
DECLARE r record; cols text; n bigint;
BEGIN
  FOR r IN
    SELECT t.table_name, substring(t.table_schema FROM 5) AS live
    FROM information_schema.tables t
    WHERE t.table_schema IN ('v10_main','v10_external','v10_nbs')
      AND t.table_type='BASE TABLE' AND t.table_name<>'patient'
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                  WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name
                    AND c.column_name='patient_id')
  LOOP
    SELECT string_agg(quote_ident(column_name), ', ') INTO cols
    FROM information_schema.columns
    WHERE table_schema='v10_'||r.live AND table_name=r.table_name AND is_identity='NO';
    EXECUTE format(
      'INSERT INTO %1$I.%2$I (%3$s) SELECT %3$s FROM v10_%1$I.%2$I v '
      'WHERE NOT EXISTS (SELECT 1 FROM %1$I.%2$I b '
      ' WHERE b.patient_id=v.patient_id '
      ' AND b.ntubiogene_sampleno IS NOT DISTINCT FROM v.ntubiogene_sampleno) '
      'AND EXISTS (SELECT 1 FROM %1$I.patient p WHERE p.patient_id=v.patient_id)',
      r.live, r.table_name, cols);
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n > 0 THEN
      RAISE NOTICE '4d insert    %.%  : % 1.0-unique rows', r.live, r.table_name, n;
    END IF;
  END LOOP;
END $$;

-- 4e. sample tables WITHOUT patient_id (cah_tgal / dmd_tsh). They link to
--     cah / dmd by the varchar business key cah_id / dmd_id, carried as-is.
--     2.0 has no rows there — plain insert; runs after 4d so the parent
--     cah / dmd rows already exist.
DO $$
DECLARE r record; cols text; n bigint;
BEGIN
  FOR r IN
    SELECT t.table_name, substring(t.table_schema FROM 5) AS live
    FROM information_schema.tables t
    WHERE t.table_schema IN ('v10_main','v10_external','v10_nbs')
      AND t.table_type='BASE TABLE' AND t.table_name<>'patient'
      AND NOT EXISTS (SELECT 1 FROM information_schema.columns c
                      WHERE c.table_schema=t.table_schema AND c.table_name=t.table_name
                        AND c.column_name='patient_id')
  LOOP
    SELECT string_agg(quote_ident(column_name), ', ') INTO cols
    FROM information_schema.columns
    WHERE table_schema='v10_'||r.live AND table_name=r.table_name AND is_identity='NO';
    EXECUTE format('INSERT INTO %1$I.%2$I (%3$s) SELECT %3$s FROM v10_%1$I.%2$I',
                   r.live, r.table_name, cols);
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n > 0 THEN RAISE NOTICE '4e insert    %.%  : % rows', r.live, r.table_name, n; END IF;
  END LOOP;
END $$;

\echo '=== COMMIT ==='
COMMIT;
