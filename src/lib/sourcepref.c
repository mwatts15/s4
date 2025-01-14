/*  S4 - An XMMS2 medialib backend
 *  Copyright (C) 2009, 2010 Sivert Berg
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Lesser General Public License for more details.
 */

#include "s4_priv.h"
#include <stdlib.h>
#include <string.h>

struct s4_sourcepref_St {
	GHashTable *table;
	GMutex lock;
	GPatternSpec **specs;
	int spec_count;
	int ref_count;
};

/**
 * @defgroup Sourcepref Source Preferences
 * @ingroup S4
 * @brief Handles source preferences
 *
 * @{
 */

/* Helper function to s4_sourcepref_get_priority */
static int _get_priority (s4_sourcepref_t *sp, const char *src)
{
	int i;
	for (i = 0; i < sp->spec_count; i++) {
		/* TODO: consider using g_pattern_spec_match instead since we're
		 * matching against multiple patterns */
		if (g_pattern_spec_match_string (sp->specs[i], src)) {
			return i;
		}
	}

	return INT_MAX;
}

/**
 * Creates a new source preferences that can be used when querying
 *
 * @param srcprefs An NULL terminated array of sources, where the
 * first one has the highest priority. The sources may use glob-
 * like patterns, for example "plugin*".
 * @return A new sourcepref
 */
s4_sourcepref_t *s4_sourcepref_create (const char **srcprefs)
{
	int i;
	s4_sourcepref_t *sp = malloc (sizeof (s4_sourcepref_t));
	sp->table = g_hash_table_new_full (g_direct_hash, g_direct_equal, NULL, free);
	g_mutex_init (&sp->lock);

	for (i = 0; srcprefs[i] != NULL; i++);

	sp->specs = malloc (sizeof (GPatternSpec*) * i);
	sp->spec_count = i;
	sp->ref_count = 1;

	for (i = 0; i < sp->spec_count; i++)
		sp->specs[i] = g_pattern_spec_new (srcprefs[i]);

	return sp;
}

/**
 * Decreases the reference of a sourcepref.
 * If the reference count is less than or equal to zero
 * it will be freed.
 * @param sp The sourcepref to free
 */
void s4_sourcepref_unref (s4_sourcepref_t *sp)
{
	int i;

	if (g_atomic_int_dec_and_test (&sp->ref_count)) {
		g_hash_table_destroy (sp->table);
		g_mutex_clear (&sp->lock);

		for (i = 0; i < sp->spec_count; i++)
			g_pattern_spec_free (sp->specs[i]);

		free (sp->specs);
		free (sp);
	}
}

/**
 * Increases the refcount of a sourcepref
 * @param sp The sourcepref to reference
 */
s4_sourcepref_t *s4_sourcepref_ref (s4_sourcepref_t *sp)
{
	g_atomic_int_inc (&sp->ref_count);
	return sp;
}

/**
 * Gets the priority of a source
 *
 * @param sp The sourcepref to check against
 * @param src The source to check
 * @return The priority of the source
 */
int s4_sourcepref_get_priority (s4_sourcepref_t *sp, const char *src)
{
	if (sp == NULL)
		return 0;

	g_mutex_lock (&sp->lock);

	int *i = g_hash_table_lookup (sp->table, src);

	if (i == NULL) {
		int pri = _get_priority (sp, src);

		i = malloc (sizeof (int));
		*i = pri;
		g_hash_table_insert (sp->table, (void*)src, i);
		g_mutex_unlock (&sp->lock);

		return pri;
	}
	g_mutex_unlock (&sp->lock);

	return *i;
}

/**
 * @}
 */
