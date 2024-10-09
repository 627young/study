//dbus头文件
// #include "Hello.h"

#include <stdio.h>
#include <gio/gio.h>


void test_string()
{
    GVariant *value1, *value2, *value3;
 
    value1 = g_variant_new ("s", "hello world!");
    value2 = g_variant_new ("o", "/must/be/a/valid/path");
    value3 = g_variant_new ("g", "iias");
 
    #if 0
    g_variant_new ("s", NULL);      /* not valid: NULL is not a string. */
    #endif
 
    {
        gchar *result;
 
        g_variant_get (value1, "s", &result);
        g_print ("value1 was '%s'\n", result);
        g_free (result);
 
        g_variant_get (value2, "o", &result);
        g_print ("value2 was '%s'\n", result);
        g_free (result);
 
        g_variant_get (value3, "g", &result);
        g_print ("value3 was '%s'\n", result);
        g_free (result);
    }
}

void test_array()
{
  GVariantBuilder *builder;
  GVariant *value;
 
  builder = g_variant_builder_new (G_VARIANT_TYPE ("as"));
  g_variant_builder_add (builder, "s", "when");
  g_variant_builder_add (builder, "s", "in");
  g_variant_builder_add (builder, "s", "the");
  g_variant_builder_add (builder, "s", "course");
 
  // These two have the same result
  value = g_variant_new ("as", builder);
  //value = g_variant_builder_end(builder);
 
  g_variant_builder_unref (builder);
 
  {
    GVariantIter *iter;
    gchar *str;
 
    g_variant_get (value, "as", &iter);
    while (g_variant_iter_loop (iter, "s", &str))
      g_print ("%s\n", str);
    g_variant_iter_free (iter);
  }
 
  g_variant_unref (value);
}

int main(int argc, char const *argv[])
{
    test_string();
    test_array();
    return 0;
}