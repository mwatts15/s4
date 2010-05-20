#include "midb.h"
#include <log.h>
#include <string.h>

/**
 * Wrapper for midb_log, writes a LOG_STRING_INSERT entry
 */
void midb_log_string_insert (s4be_t *be, int32_t id, const char *string)
{
	log_entry_t entry;
	entry.type = LOG_STRING_INSERT;
	entry.data.str.str = string;
	entry.data.str.id = id;
	midb_log (be, &entry);
}

/**
 * Wrapper for midb_log, writes a LOG_PAIR_INSERT entry
 */
void midb_log_pair_insert (s4be_t *be, bpt_record_t *rec)
{
	log_entry_t entry;
	entry.type = LOG_PAIR_INSERT;
	entry.data.pair = rec;
	midb_log (be, &entry);
}

/**
 * Wrapper for midb_log, writes a LOG_PAIR_REMOVE entry
 */
void midb_log_pair_remove (s4be_t *be, bpt_record_t *rec)
{
	log_entry_t entry;
	entry.type = LOG_PAIR_REMOVE;
	entry.data.pair = rec;
	midb_log (be, &entry);
}

/**
 * Write a log entry.
 */
void midb_log (s4be_t *be, log_entry_t *entry)
{
	int32_t tmp;

	if (be->logfile == NULL)
		return;

	fwrite (&entry->type, sizeof(int32_t), 1, be->logfile);
	switch (entry->type) {
		case LOG_STRING_INSERT:
			tmp = strlen (entry->data.str.str);
			fwrite (&entry->data.str.id, sizeof (int32_t), 1, be->logfile);
			fwrite (&tmp, sizeof (int32_t), 1, be->logfile);
			fwrite (entry->data.str.str, 1, tmp, be->logfile);
			break;
		case LOG_PAIR_INSERT:
		case LOG_PAIR_REMOVE:
			fwrite (entry->data.pair, sizeof (bpt_record_t), 1, be->logfile);
			break;
		default:
			S4_DBG ("Trying to write a log entry with invalid type");
			break;
	}
}
