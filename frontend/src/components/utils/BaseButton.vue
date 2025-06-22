<template>
  <button :class="['btn', variantClass]"
          v-on="$attrs">
    <span v-if="iconComponent" class="icon" aria-hidden="true">
      <component :is="iconComponent" />
    </span>
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue';
import { PlusIcon, PencilIcon, TrashIcon, XMarkIcon, TvIcon } from '@heroicons/vue/20/solid';

const props = defineProps({
  variant: {
    type: String,
    default: 'create',
    validator: (val) => ['create', 'update', 'delete', 'close', 'view'].includes(val),
  },
  icon: {
    type: [Object, Function],
    default: null,
  }
});

const iconComponent = computed(() => {
  if (props.icon) return props.icon;
  if (props.variant === 'create') return PlusIcon;
  if (props.variant === 'update') return PencilIcon;
  if (props.variant === 'delete') return TrashIcon;
  if (props.variant === 'close') return XMarkIcon;
  if (props.variant === 'view') return TvIcon;
  return null;
});

const variantClass = computed(() => `btn-${props.variant}`);
</script>

<style scoped>
.btn {
  padding: 10px 16px;
  font-size: 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s ease;
  min-width: 100px;
  text-align: center;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-create {
  background-color: #3490dc;
  color: white;
}
.btn-create:hover {
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

.icon {
  display: flex;
  align-items: center;
}

.icon :deep(svg) {
  width: 18px;
  height: 18px;
}
</style>
