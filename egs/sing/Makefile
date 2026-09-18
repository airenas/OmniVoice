cfg?=Makefile.options
-include $(cfg)

#####################################################################################
#### INFO
#####################################################################################
info:
	@echo "work_dir: 		$(work_dir)"
	@echo "corpus_bucket: 	$(corpus_bucket)"
	@echo "corpus_dir: 		$(corpus_dir)"
	@echo "config: 			$(config)"
	@echo "finetune_output:	$(finetune_output)"
	@echo "type: 			$(type)"
	@echo "nvidia-smi: 		$$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv | tail -n1)"
	@echo "cuda visible dev: 	$$(echo $$CUDA_VISIBLE_DEVICES)"
	@echo "python: 			$$(python --version)"
	@echo "torch: 			$$(python -c 'import torch; print(torch.__version__)')"
	@echo "torchaudio: 		$$(python -c 'import torchaudio; print(torchaudio.__version__)')"
	@echo "cuda in python: 	$$(python -c 'import torch; print(torch.version.cuda) if torch.cuda.is_available() else "N/A"')"
.PHONY: info	
#####################################################################################
log?=INFO
python_cmd=PYTHONPATH=./ LOGLEVEL=$(log) python3
python_omni_cmd=PYTHONPATH=./../../ LOGLEVEL=$(log) python3
#####################################################################################
#####################################################################################
#### PREPARE CORPUS
#####################################################################################
#####################################################################################
$(work_dir) $(corpus_dir)/extracted $(corpus_dir)/lab $(corpus_dir)/range \
		$(corpus_dir)/final $(corpus_dir)/final/wavs $(corpus_dir)/wav \
		$(work_dir)/finetune/data $(work_dir)/finetune/exp/omnivoice_finetune \
		$(work_dir)/corpus:
	mkdir -p $@
#####################################################################################
speaker?=NER
lab_prefix?=NER
freq?=24000

$(corpus_dir)/.dwn.done: | $(work_dir)
	mcli cp $(corpus_bucket) $(corpus_dir)/dwn/ -r
	touch $@
############################################
$(corpus_dir)/extracted/utf8.mlf: $(corpus_dir)/.dwn.done | $(corpus_dir)/extracted
	iconv -f ISO-8859-13 -t UTF-8 $(corpus_dir)/dwn/metadata.mlf > $@
############################################
$(corpus_dir)/extracted/fixed.mlf: $(corpus_dir)/extracted/utf8.mlf | $(corpus_dir)/lab
	pv $^ | $(python_cmd) ./local/exclude_files.py --exclude "$(exclude_files)" \
		| $(python_cmd) ./local/fix_mlf.py \
		| $(python_cmd) ./local/change_name.py --prefix '$(speaker)_' --strip-prefix '$(lab_prefix)' > $@
############################################
$(corpus_dir)/extracted/fixed.split.mlf: $(corpus_dir)/extracted/fixed.mlf $(corpus_dir)/range/.done
	pv $(corpus_dir)/extracted/fixed.mlf | $(python_cmd) ./local/mlf_by_range.py --rangeDir $(corpus_dir)/range > $@_
	mv $@_ $@
############################################
$(corpus_dir)/lab/.done: $(corpus_dir)/extracted/fixed.mlf | $(corpus_dir)/lab
	pv $^ | $(python_cmd) ./local/split_mlf.py --outDir `dirname $@`
	touch $@
############################################
$(corpus_dir)/range/.done: $(corpus_dir)/lab/.done | $(corpus_dir)/range
	ls -1 $(corpus_dir)/lab/*.lab | xargs -n1 -I {} -P 4 sh -c \
		'base=`basename {} .lab`; \
		cat {} | $(python_cmd) ./local/mlf_to_range.py --max-sil 400 --max-duration 20000 > $(corpus_dir)/range/$${base}.split.range'
	touch $@
############################################
$(corpus_dir)/wav/split.sh: $(corpus_dir)/range/.done | $(corpus_dir)/wav
	rm -f $@_
	ls -1 $(corpus_dir)/range/*.range | xargs -n1 -I {} sh -c \
		'base=`basename {} .split.range`; \
		cat {} | $(python_cmd) ./local/range_to_split_sh.py --name $${base} --in-dir $(corpus_wav_dir) --out-dir $(corpus_dir)/wav \
			--strip-prefix '$(speaker)_' >> $@_'
	mv $@_ $@	
	chmod +x $@
############################################
$(corpus_dir)/wav/.done: $(corpus_dir)/wav/split.sh
	$(corpus_dir)/wav/split.sh
	touch $(corpus_dir)/wav/.done
############################################
$(corpus_dir)/extracted/metadata.csv: $(corpus_dir)/extracted/fixed.split.mlf
	pv $< | $(python_cmd) ./local/mlf_to_csv.py --outputPhones --skipSP > $@_
	mv $@_ $@
$(corpus_dir)/final/metadata.csv: $(corpus_dir)/extracted/metadata.csv | $(corpus_dir)/final
	pv $< | sed '/noise/d' | sort > $@_
	mv $@_ $@

############################################
$(corpus_dir)/extracted/audio.samples: $(work_dir)/final/wavs/.done
	ls -1 $(corpus_dir)/final/wavs/*.wav | sort | pv | $(python_cmd) ./local/audio_to_samples.py > $@_
	mv $@_ $@
############################################
$(corpus_dir)/extracted/exclude.files: $(corpus_dir)/extracted/metadata.csv
	cat $< | grep 'noise' | awk -F'|' '{print $$1}' > $@_
	mv $@_ $@
############################################
$(corpus_dir)/final/wavs/.done: $(corpus_dir)/wav/.done $(corpus_dir)/extracted/exclude.files | $(corpus_dir)/final/wavs
	for wav in $(corpus_dir)/wav/*.wav; do \
		base=`basename $${wav} .wav`; \
		base=$$(echo $${base} | sed s/lab_//g); \
# 		echo "Copy wav $${base}"; \
# 		cp $${wav} $(corpus_dir)/final/wavs/$${base}.wav; \
		echo "Converting WAV to $(freq) Hz 16 bit for $${base}"; \
		sox $${wav} -r $(freq) -b 16 $(corpus_dir)/final/wavs/$${base}.wav; \
	done
	echo "Drop exluded files"
	cat $(corpus_dir)/extracted/exclude.files | xargs -n 1 -I {} sh -c 'rm $(corpus_dir)/final/wavs/{}.wav'
	touch $(corpus_dir)/final/wavs/.done
############################################
test/corpus/len: $(corpus_dir)/final/wavs/.done
	ls -1 $(corpus_dir)/final/wavs/*.wav | xargs -n1 soxi -D | $(python_local_cmd) -c "import sys; print(f'{sum(float(x) for x in sys.stdin)/3600:.3f}h')"
############################################
type ?= gr
$(corpus_dir)/.prepare.done: $(corpus_dir)/final/metadata.csv $(corpus_dir)/final/wavs/.done
	touch $@
$(work_dir)/corpus/all.jsonl: $(corpus_dir)/.prepare.done | $(work_dir)/corpus
	$(python_cmd) ./local/csv_to_jsonl.py --input $(corpus_dir)/final/metadata.csv --output $(work_dir)/corpus/all.jsonl_ \
		--audio-dir $(corpus_dir)/final/wavs --type=$(type)
	mv $(work_dir)/corpus/all.jsonl_ $(work_dir)/corpus/all.jsonl

prepare/corpus: $(corpus_dir)/.prepare.done
.PHONY: prepare/corpus

$(work_dir)/corpus/dev.jsonl $(work_dir)/corpus/train.jsonl: $(work_dir)/corpus/all.jsonl
	$(python_cmd) ./local/split_jsonl.py --input $(work_dir)/corpus/all.jsonl --dev-output $(work_dir)/corpus/dev.jsonl_ \
		--train-output $(work_dir)/corpus/train.jsonl_
	mv $(work_dir)/corpus/dev.jsonl_ $(work_dir)/corpus/dev.jsonl
	mv $(work_dir)/corpus/train.jsonl_ $(work_dir)/corpus/train.jsonl

prepare/json: $(work_dir)/corpus/dev.jsonl $(work_dir)/corpus/train.jsonl
.PHONY: prepare/json

#####################################################################################
#### PREPARE FOR FINETUNE
#####################################################################################
$(work_dir)/finetune/data/.%.prepare.done: $(work_dir)/corpus/%.jsonl $(corpus_dir)/.prepare.done | $(work_dir)/finetune/data
	$(python_omni_cmd) -m omnivoice.scripts.extract_audio_tokens \
            --input_jsonl "$(work_dir)/corpus/$*.jsonl" \
			--tar_output_pattern "$(work_dir)/finetune/data/$*/audios/shard-%06d.tar" \
			--jsonl_output_pattern "$(work_dir)/finetune/data/$*/txts/shard-%06d.jsonl" \
            --tokenizer_path eustlb/higgs-audio-v2-tokenizer \
            --nj_per_gpu 3 --shuffle True
	touch $@
prepare/finetune: $(work_dir)/finetune/data/.dev.prepare.done $(work_dir)/finetune/data/.train.prepare.done
.PHONY: prepare/finetune
#####################################################################################
#####################################################################################
config?=./config/train.config.json
finetune_output?=$(work_dir)/finetune/exp/omnivoice_finetune

$(work_dir)/finetune/data.json: $(work_dir)/finetune/data/.dev.prepare.done $(work_dir)/finetune/data/.train.prepare.done | $(work_dir)/finetune
	printf '%s\n' '{"train": [{"manifest_path": ["$(work_dir)/finetune/data/train/data.lst"]}],' \
	'  "dev": [{"manifest_path": ["$(work_dir)/finetune/data/dev/data.lst"]}]}' > $@

finetune: $(work_dir)/finetune/.done
GPU_IDS?=0,1,2
NUM_GPUS?=3
$(work_dir)/finetune/.done: $(work_dir)/finetune/data/.train.prepare.done $(work_dir)/finetune/data.json | $(work_dir)/finetune/exp/omnivoice_finetune
	accelerate launch --gpu_ids "${GPU_IDS}" --num_processes ${NUM_GPUS} -m omnivoice.cli.train \
		--train_config $(config) \
        --data_config $(work_dir)/finetune/data.json \
        --output_dir $(finetune_output)
#####################################################################################
jupyter: 
	jupyter lab ./ --ip=0.0.0.0 --port=8888 --no-browser		
#####################################################################################
clean:
	@echo -n "Are you sure to delete $(work_dir)? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(work_dir)
.PHONY: clean
clean/corpus/tmp:
	@echo -n "Are you sure to delete $(corpus_dir) tmp data? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -rf $(corpus_dir)/wav/*.wav $(corpus_wav_dir)/*.wav

.PHONY: clean
#####################################################################################
.EXPORT_ALL_VARIBLES:	
