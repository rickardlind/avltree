/* AVL tree Python module */

#include <Python.h>


/* Tree node.
 */
struct Node {
    PyObject     *element;
    struct Node  *left;
    struct Node  *right;
    unsigned int  height;
};


/* AVLTree class
 */
struct AVLTree {
    PyObject_HEAD

    struct Node *root;
};


/* Entry state.
 */
enum State {
    STATE_LEFT,
    STATE_ELEMENT,
    STATE_RIGHT,
    STATE_UP,
};


/* Iterator entry
 */
struct Entry {
    struct Node  *node;
    enum State    state;
};


/* Max stack depth (tree height).
 */
enum Stack {
    STACK_MAX = 64,
};


/* Iterator.
 */
struct Iterator {
    PyObject_HEAD

    struct AVLTree  *tree;
    struct Entry     stack[STACK_MAX];
    unsigned int     count;
};


static int AVLTree_init(struct AVLTree *self, PyObject *args, PyObject *kwargs);
static void AVLTree_dealloc(struct AVLTree *self);
static PyObject *AVLTree_iter(struct AVLTree *self);
static PyObject *AVLTree_insert(struct AVLTree *self, PyObject *element);
static PyObject *AVLTree_delete(struct AVLTree *self, PyObject *element);
static PyObject *AVLTree_to_tuple(struct AVLTree *self, PyObject *);
static PyObject *AVLTree_getheight(struct AVLTree *self, void *);

static int Iterator_init(struct Iterator *self, PyObject *args, PyObject *kwargs);
static void Iterator_dealloc(struct Iterator *self);
static PyObject *Iterator_next(struct Iterator *self);

static struct Node *node_alloc(PyObject *element);
static void node_dealloc(struct Node *node);
static inline unsigned int node_height(struct Node *node);
static unsigned int node_update_height(struct Node *node);
static inline int node_balance_factor(struct Node *node);
static struct Node *node_rotate_left(struct Node *node);
static struct Node *node_rotate_right(struct Node *node);
static PyObject *node_to_tuple(struct Node *node);


#define STACK_PUSH(stk, cnt, elt)			\
    do {						\
        if ((cnt) < STACK_MAX) {			\
	    (stk)[(cnt)++] = (elt);			\
	}						\
	else {						\
	    PyErr_SetString(PyExc_RuntimeError,		\
			    "stack overflow");		\
	    goto cleanup;				\
	}						\
    } while(0)


static PyMethodDef AVLTREE_METHODS[] = {
    { "insert",   (PyCFunction)AVLTree_insert,   METH_O,      "Insert element" },
    { "delete",   (PyCFunction)AVLTree_delete,   METH_O,      "Delete element" },
    { "to_tuple", (PyCFunction)AVLTree_to_tuple, METH_NOARGS, "Return tree as tuples" },
    { NULL } /* Sentinel */
};


static PyGetSetDef AVLTREE_GETSETTERS[] = {
    { "height", (getter) AVLTree_getheight, NULL, "Tree height", NULL},
    { NULL }  /* Sentinel */
};


static PyTypeObject AVLTREE_TYPE = {
    PyVarObject_HEAD_INIT(NULL, 0)

    .tp_name      = "cavltree.AVLTree",
    .tp_doc       = "AVLTree objects",
    .tp_basicsize = sizeof(struct AVLTree),
    .tp_itemsize  = 0,
    .tp_flags     = Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,
    .tp_new       = PyType_GenericNew,
    .tp_init      = (initproc) AVLTree_init,
    .tp_dealloc   = (destructor) AVLTree_dealloc,
    .tp_iter      = (getiterfunc) AVLTree_iter,
    .tp_methods   = AVLTREE_METHODS,
    .tp_getset    = AVLTREE_GETSETTERS,
};


static PyTypeObject ITERATOR_TYPE = {
    PyVarObject_HEAD_INIT(NULL, 0)

    .tp_name      = "cavltree.Iterator",
    .tp_doc       = "AVLTree iterator",
    .tp_basicsize = sizeof(struct Iterator),
    .tp_itemsize  = 0,
    .tp_flags     = Py_TPFLAGS_DEFAULT,
    .tp_new       = PyType_GenericNew,
    .tp_init      = (initproc) Iterator_init,
    .tp_dealloc   = (destructor) Iterator_dealloc,
    .tp_iter      = PyObject_SelfIter,
    .tp_iternext  = (iternextfunc) Iterator_next,
};


static PyModuleDef CAVLTREE_MODULE = {
    PyModuleDef_HEAD_INIT,

    .m_name = "cavltree",
    .m_doc  = "AVL tree extension type.",
    .m_size = -1,
};


PyMODINIT_FUNC PyInit_cavltree(void)
{
    PyObject *m = NULL, *rv = NULL;

    if (PyType_Ready(&AVLTREE_TYPE) == -1 ||
	PyType_Ready(&ITERATOR_TYPE) == -1) {
        goto cleanup;
    }

    if ((m = PyModule_Create(&CAVLTREE_MODULE)) == NULL) {
        goto cleanup;
    }

    Py_INCREF(&AVLTREE_TYPE);

    if (PyModule_AddObject(m, "AVLTree", (PyObject *) &AVLTREE_TYPE) == -1) {
	goto cleanup;
    }

    rv = m;
    m = NULL;

 cleanup:
    if (m != NULL) {
	Py_DECREF(m);
	Py_DECREF(&AVLTREE_TYPE);
    }

    return rv;
}


static int AVLTree_init(struct AVLTree *self, PyObject *args, PyObject *kwargs)
{
    static char *KWDS[] = { "iterable", NULL };
    PyObject *iterable = NULL, *iterator = NULL, *element = NULL, *result = NULL;
    int rv = -1;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", KWDS, &iterable)) {
	goto cleanup;
    }

    if (iterable != NULL) {
	if ((iterator = PyObject_GetIter(iterable)) == NULL) {
	    goto cleanup;
	}

	while ((element = PyIter_Next(iterator)) != NULL) {
	    result = AVLTree_insert(self, element);
	    Py_DECREF(element);

	    if (result == NULL) {
		goto cleanup;
	    }

	    Py_DECREF(result);
	}

	if (PyErr_Occurred()) {
	    goto cleanup;
	}
    }

    rv = 0;

 cleanup:
    Py_XDECREF(iterator);

    return rv;
}


static void AVLTree_dealloc(struct AVLTree *self)
{
    node_dealloc(self->root);
    Py_TYPE(self)->tp_free((PyObject *) self);
}


static PyObject *AVLTree_iter(struct AVLTree *self)
{
    return PyObject_CallFunction((PyObject *) &ITERATOR_TYPE, "O", self);
}


static PyObject *AVLTree_insert(struct AVLTree *self,
				PyObject *element)
{
    struct Node **stack[STACK_MAX] = { 0 }, **side = NULL, *node = NULL;
    unsigned int count = 0, old = 0;
    int res = -1, bf = 0;
    PyObject *rv = NULL;

    side = &self->root;

    while ((node = *side) != NULL) {
	STACK_PUSH(stack, count, side);

	/* element < node->element ==> left */
	if ((res = PyObject_RichCompareBool(element, node->element, Py_LT)) == -1) {
	    goto cleanup;
	}

	if (res) {
	    side = &node->left;
	    continue;
	}

	/* node->element < element ==> right */
	if ((res = PyObject_RichCompareBool(node->element, element, Py_LT)) == -1) {
	    goto cleanup;
	}

	if (res) {
	    side = &node->right;
	    continue;
	}

	/* equal ==> return element */
	rv = node->element;
	goto cleanup;
    }

    if ((node = node_alloc(element)) == NULL) {
	goto cleanup;
    }

    *side = node;

    while (count > 0) {
	side = stack[--count];
	node = *side;
	old = node_update_height(node);
	bf = node_balance_factor(node);

	if (bf == 2) {
	    if (node_balance_factor(node->right) < 0) {
		node->right = node_rotate_right(node->right);
	    }

	    *side = node_rotate_left(node);
	}
	else if (bf == -2) {
	    if (node_balance_factor(node->left) > 0) {
		node->left = node_rotate_left(node->left);
	    }

	    *side = node_rotate_right(node);
	}
	else if (node->height == old) {
	    break;
	}
    }

    rv = Py_None;

 cleanup:
    Py_XINCREF(rv);

    return rv;
}


static PyObject *AVLTree_delete(struct AVLTree *self,
				PyObject *element)
{
    struct Node **stack[STACK_MAX] = { 0 }, **side = NULL, *node = NULL;
    unsigned int count = 0, old = 0;
    int res = -1, bf = 0;
    PyObject *rv = NULL;

    side = &self->root;

    while ((node = *side) != NULL) {
	STACK_PUSH(stack, count, side);

	/* element < node->element ==> left */
	if ((res = PyObject_RichCompareBool(element, node->element, Py_LT)) == -1) {
	    goto cleanup;
	}

	if (res) {
	    side = &node->left;
	    continue;
	}

	/* node->element < element ==> right */
	if ((res = PyObject_RichCompareBool(node->element, element, Py_LT)) == -1) {
	    goto cleanup;
	}

	if (res) {
	    side = &node->right;
	    continue;
	}

	break; /* equal ==> found */
    }

    if (node == NULL) {
	Py_RETURN_NONE;
    }

    if (node->left != NULL && node->right != NULL) {
	struct Node *target = node;

	side = &node->right;
	node = *side;

	STACK_PUSH(stack, count, side);

	while (node->left != NULL) {
	    side = &node->left;
	    node = *side;

	    STACK_PUSH(stack, count, side);
	}

	if (node->right != NULL) {
	    *side = node->right;
	    node->right = NULL;
	}
	else {
	    *side = NULL;
	}

	rv = target->element;
	target->element = node->element;
	node->element = NULL;
    }
    else {
	if (node->left != NULL) {
	    *side = node->left;
	    node->left = NULL;
	}
	else if (node->right != NULL) {
	    *side = node->right;
	    node->right = NULL;
	}
	else {
	    *side = NULL;
	}

	rv = node->element;
	node->element = NULL;
    }

    node_dealloc(node);

    if (*side == NULL) {
	--count;
    }

    while (count > 0) {
	side = stack[--count];
	node = *side;
	old = node_update_height(node);
	bf = node_balance_factor(node);

	if (bf == 2) {
	    if (node_balance_factor(node->right) < 0) {
		node->right = node_rotate_right(node->right);
	    }

	    *side = node_rotate_left(node);
	}
	else if (bf == -2) {
	    if (node_balance_factor(node->left) > 0) {
		node->left = node_rotate_left(node->left);
	    }

	    *side = node_rotate_right(node);
	}
	else if (node->height == old) {
	    break;
	}
    }

 cleanup:
    return rv;
}


static PyObject *AVLTree_to_tuple(struct AVLTree *self,
				  PyObject *Py_UNUSED(ignored))
{
    return node_to_tuple(self->root);
}


static PyObject *AVLTree_getheight(struct AVLTree *self,
				   void *Py_UNUSED(ignored))
{
    return PyLong_FromUnsignedLong(node_height(self->root));
}


static int Iterator_init(struct Iterator *self, PyObject *args, PyObject *kwargs)
{
    static char *KWDS[] = { "tree", NULL };
    PyObject *tree = NULL;
    int rv = -1;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", KWDS, &tree)) {
	goto cleanup;
    }

    Py_INCREF(tree);
    self->tree = (struct AVLTree *)tree;

    if (self->tree->root != NULL) {
	self->stack[0].node = self->tree->root;
	self->stack[0].state = STATE_LEFT;
	self->count = 1;
    }
    else {
	self->count = 0;
    }

    rv = 0;

 cleanup:
    return rv;
}


static void Iterator_dealloc(struct Iterator *self)
{
    Py_XDECREF(self->tree);
    Py_TYPE(self)->tp_free((PyObject *) self);
}


static PyObject *Iterator_next(struct Iterator *self)
{
    PyObject *element = NULL;
    struct Entry *entry = NULL;
    struct Node *next = NULL;

    do  {
	if (self->count == 0) {
	    PyErr_SetNone(PyExc_StopIteration);
	    break;
	}

	if (next == NULL) {
	    entry = &self->stack[ self->count - 1 ];
	}
	else if (self->count < STACK_MAX) {
	    entry = &self->stack[ self->count++ ];
	    entry->node = next;
	    entry->state = STATE_LEFT;
	}
	else {
	    PyErr_SetString(PyExc_RuntimeError, "stack overflow");
	    break;
	}

	switch (entry->state) {
	case STATE_LEFT:
	    entry->state = STATE_ELEMENT;
	    next = entry->node->left;
	    break;

	case STATE_ELEMENT:
	    entry->state = STATE_RIGHT;
	    element = entry->node->element;
	    Py_INCREF(element);
	    break;

	case STATE_RIGHT:
	    entry->state = STATE_UP;
	    next = entry->node->right;
	    break;

	case STATE_UP:
	    self->count--;
	    next = NULL;
	    break;
	}
    } while (element == NULL);

    return element;
}


static struct Node *node_alloc(PyObject *element)
{
    struct Node *node = NULL;

    if ((node = calloc(1, sizeof *node)) == NULL) {
	PyErr_NoMemory();
	goto cleanup;
    }

    Py_INCREF(element);
    node->element = element;
    node->height  = 1;

 cleanup:
    return node;
}


static void node_dealloc(struct Node *node)
{
    if (node != NULL) {
	node_dealloc(node->left);
	node_dealloc(node->right);
	Py_XDECREF(node->element);
	free(node);
    }
}


static inline unsigned int node_height(struct Node *node)
{
    return node ? node->height : 0;
}


static unsigned int node_update_height(struct Node *node)
{
    unsigned int rv = 0;

    rv = node->height;

    node->height = 1 + Py_MAX(node_height(node->left),
			      node_height(node->right));

    return rv;
}


static inline int node_balance_factor(struct Node *node)
{
    return node_height(node->right) - node_height(node->left);
}


static struct Node *node_rotate_left(struct Node *node)
{
    struct Node *root = NULL;

    root = node->right;
    node->right = root->left;
    root->left = node;

    node_update_height(node);
    node_update_height(root);

    return root;
}


static struct Node *node_rotate_right(struct Node *node)
{
    struct Node *root = NULL;

    root = node->left;
    node->left = root->right;
    root->right = node;

    node_update_height(node);
    node_update_height(root);

    return root;
}


static PyObject *node_to_tuple(struct Node *node)
{
    PyObject *l = NULL, *r = NULL, *e = NULL, *h = NULL, *t = NULL;

    if (node == NULL) {
	Py_RETURN_NONE;
    }

    if ((l = node_to_tuple(node->left)) == NULL) {
	goto cleanup;
    }

    if ((r = node_to_tuple(node->right)) == NULL) {
	goto cleanup;
    }

    e = node->element;
    Py_INCREF(e);

    if ((h = PyLong_FromUnsignedLong(node->height)) == NULL) {
	goto cleanup;
    }

    if ((t = PyTuple_Pack(4, l, e, h, r)) == NULL) {
	goto cleanup;
    }

    l = r = e = h = NULL;

 cleanup:
    Py_XDECREF(l);
    Py_XDECREF(r);
    Py_XDECREF(e);
    Py_XDECREF(h);

    return t;
}
