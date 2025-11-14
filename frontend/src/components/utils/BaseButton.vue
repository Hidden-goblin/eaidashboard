<template>
  <component
      :is="to ? RouterLink : 'button'"
      :to="to"
      :class="[styles.btnBase, variantClass, { 'btn-icon-only': iconOnly }]"
      v-on="listeners"
      v-bind="attrsOnly"
  >
    <span v-if="iconComponent" class="icon" aria-hidden="true">
      <component :is="iconComponent"/>
    </span>
    <slot/>
  </component>
</template>

<script setup>
import {computed, useAttrs} from 'vue';
import {RouterLink} from 'vue-router';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
  TvIcon,
  GlobeAltIcon,
  AcademicCapIcon
} from '@heroicons/vue/20/solid';
import styles from '@/styles/buttons.module.css'

const props = defineProps({
  to: String,
  variant: {
    type: String,
    default: 'clear',
    validator: (val) => ['create', 'update', 'delete', 'close', 'view', 'navigate', 'admin', 'clear'].includes(val),
  },
  icon: {
    type: [Object, Function],
    default: null,
  },
  iconOnly:{
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: 'button',
    validator: (val) => ['button', 'submit', 'reset'].includes(val),
  }
});

const rawAttrs = useAttrs();

// separate listeners vs attributes
const listeners = computed(() =>
    Object.fromEntries(Object.entries(rawAttrs).filter(([key]) => key.startsWith('on')))
);

const attrsOnly = computed(() => {
  const base = Object.fromEntries(Object.entries(rawAttrs).filter(([key]) => !key.startsWith('on')));
  if (!props.to) {
    base.type = props.type;
  }
  return base;
});

const iconComponent = computed(() => {
  if (props.icon) return props.icon;
  if (props.variant === 'create') return PlusIcon;
  if (props.variant === 'update') return PencilIcon;
  if (props.variant === 'delete') return TrashIcon;
  if (props.variant === 'close') return XMarkIcon;
  if (props.variant === 'navigate') return GlobeAltIcon;
  if (props.variant === 'admin') return AcademicCapIcon;
  if (props.variant === 'view') return TvIcon;
  return null;
});

const variantClass = computed(() => `btn-${props.variant}`);
</script>

<style scoped>

.btn-create,
.btn-navigate {
  background-color: #3490dc;
  color: white;
}

.btn-create:hover,
.btn-navigate:hover {
  background-color: #2779bd;
}

.btn-update {
  background-color: #38c172;
  color: white;
}

.btn-update:hover {
  background-color: #1f9d55;
}

.btn-delete {
  background-color: #e3342f;
  color: white;
}

.btn-delete:hover {
  background-color: #cc1f1a;
}

.btn-close {
  background-color: #e3342f;
  color: white;
}

.btn-close:hover {
  background-color: #cc1f1a;
}

.btn-view {
  background-color: #bdbdbd;
  color: white;
}

.btn-view:hover {
  background-color: #8f8f8f;
}

.btn-admin {
  background-color: #fbb869;
  color: white;
}

.btn-admin:hover {
  background-color: #936c3f;
}

.btn-clear {
  background-color: transparent;
  color: #6c757d;
  border: 1px solid #6c757d;
}

.btn-clear:hover {
  background-color: #f8f9fa;
  color: #495057;
}

a {
  text-decoration: none;
}

.icon {
  display: flex;
  align-items: center;
}

.icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.btn-icon-only {
  padding: 0;
  border: none;
  width: auto;
  height: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-icon-only .icon :deep(svg) {
  width: 20px;
  height: 20px;
}
</style>
